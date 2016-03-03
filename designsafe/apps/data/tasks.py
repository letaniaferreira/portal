from __future__ import absolute_import

from celery import shared_task
from designsafe.celery import app
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from designsafe.libs.elasticsearch.api import Object
from dsapi.agave import utils as agave_utils
from dsapi.agave.daos import AgaveMetaFolderFile, FileManager, AgaveFolderFile
from designsafe.apps.data.apps import DataEvent
from designsafe.apps.signals.signals import generic_event
from agavepy.agave import Agave
import logging

logger = logging.getLogger(__name__)


@shared_task
def index_job_outputs(data):
    logger.debug('Preparing to index Job outputs: %s' % data)

    job_owner = data['job_owner']
    job_id = data['job_id']

    if data['status'] == 'INDEXING':
        try:
            user = get_user_model().objects.get(username=job_owner)
            if user.agave_oauth.expired:
                user.agave_oauth.refresh()
            ag = Agave(api_server=settings.AGAVE_TENANT_BASEURL,
                       token=user.agave_oauth.token['access_token'])
            job = ag.jobs.get(jobId=job_id)
            system_id = job['archiveSystem']
            archive_path = job['archivePath']
            #base_file = ag.files.list(systemId=system_id, filePath=archive_path)
            # the listing returns "name"="." for the first folder in the list
            # we need the actual folder name
            #base_file[0]['name'] = base_file[0]['path'].split('/')[-1]
            #get_or_create_from_file(ag, base_file[0])
            for f in agave_utils.fs_walk(ag, system_id, archive_path):
                fo = agave_utils.get_folder_obj(agave_client = ag, file_obj = f)
                logger.debug('Indexing: {}'.format(fo.full_path))
                o = Object(**fo.to_dict())
                o.save()

            paths = archive_path.split('/')
            for i in range(len(paths)):
                path = '/'.join(paths)
                fo = AgaveFolderFile.from_path(ag, system_id, path)
                logger.debug('Indexing: {}'.format(fo.full_path))
                o = Object(**fo.to_dict())
                o.save()
                paths.pop()

            data['status']='FINISHED'
            generic_event.send_robust(None, event_type='job', event_data=data,
                                      event_users=[username])

        except ObjectDoesNotExist:
            logger.exception('Unable to locate local user=%s' % job_owner)

@app.task
def share(system_id, path, username, permission, me):
    logger.debug('Sharing file/folder: {}. To: {}. Owner: {}'.format(path, username, me))
    try:
        user = get_user_model().objects.get(username=me)
        if user.agave_oauth.expired:
            user.agave_oauth.refresh()
        ag = Agave(api_server=settings.AGAVE_TENANT_BASEURL,
                   token = user.agave_oauth.token['access_token'])
        mngr = FileManager(agave_client = ag)
        rep = mngr.share(system_id = system_id, path = path,
                  username = username, permission = permission,
                  me = me)
        logger.debug('Successfully updated permissions: {}'.format(rep))

        DataEvent.send_generic_event({
                  'username_from': me,
                  'username_to': username,
                  'permission': permission,
                  'action': 'share_start',
                  'path': path,
                  'action_link': { 'label': 'View Files', 'value': '/data/my/#/Shared with me/' + self.file_path},
                  'html':[
                      {'label': '<b>Sharing Sarting</b>', 'value':'share_start'},
                      { 'label': 'Shared with', 'value': username},
                      { 'label': 'Permissions set', 'value': permission},
                      {'label': 'Message' , 'value': 'Your files are being shared.'},

                      ]
                  },
                  [me])

        DataEvent.send_generic_event({
                  'username_from': request.user.username,
                  'username_to': user,
                  'permission': permission,
                  'action': 'share_start',
                  'path': self.file_path,
                  'action_link': { 'label': 'View Files', 'value': '/data/my/#/Shared with me/' + self.file_path},
                  'html':[
                      {'label': '<b>Sharing Sarting</b>', 'value':'share_start'},
                      { 'label': 'Shared with', 'value': user},
                      { 'label': 'Permissions set', 'value': permission},
                      {'label': 'Message' , 'value': 'Your files are being shared.'},
                      ]
                  }
                  [username])
    except ObjectDoesNotExist:
        logger.exception('Unable to locate local user=%s' % job_owner)
