(function(window, angular, $, _) {
  "use strict";
  angular.module('WorkspaceApp').factory('Apps', ['$http', 'djangoUrl', function($http, djangoUrl) {

    var service = {};

    var default_list_opts = {
      publicOnly: false
    };
    service.list = function(opts) {
      opts = opts || {};
      var params = _.extend(default_list_opts, opts);
      return $http({
        url: djangoUrl.reverse('designsafe_workspace:call_api', ['apps']),
        method: 'GET',
        params: params
      });
    };

    service.get = function(app_id) {
      return $http({
        url: djangoUrl.reverse('designsafe_workspace:call_api', ['apps']),
        method: 'GET',
        params: {'app_id': encodeURIComponent(app_id)}
      });
    };

    service.formSchema = function(app) {
      if (typeof app === 'string') {
        app = service.get(app);
      }
      var params = app.parameters || [];
      var inputs = app.inputs || [];

      var schema = {
        type: 'object',
        properties: {
          name: {
            title: 'Job name',
            description: 'A recognizable name for this job',
            type: 'string'
          }
        }
      };

      if (params.length > 0) {
        schema.properties.parameters = {
          type: 'object',
          title: 'Parameters',
          properties: {}
        };
        _.each(params, function(param) {
          var field = {
            title: param.details.label,
            description: param.details.description
          };
          switch (param.value.type) {
            case 'bool':
            case 'flag':
              field.type = 'boolean';
              break;

            case 'enumeration':
              field.type = 'string';
              field.enum = _.map(param.value.enum_values, function(enum_val) {
                return Object.keys(enum_val)[0];
              });
              // field.titleMap = param.value.enum_values;
              break;

            case 'number':
              field.type = 'number';
              break;

            case 'string':
            default:
              field.type = 'string';
          }
          schema.properties.parameters.properties[param.id] = field;
        });
      }

      if (inputs.length > 0) {
        schema.properties.inputs = {
          type: 'object',
          title: 'Inputs',
          properties: {}
        };
        _.each(inputs, function(input) {
          var field = {
            title: input.details.label,
            description: input.details.description,
            type: 'string'
          };
          schema.properties.inputs.properties[input.id] = field;
        });
      }

      return schema;
    };

    return service;
  }]);

})(window, angular, jQuery, _);