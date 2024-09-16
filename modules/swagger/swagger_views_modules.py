""" OpenAPI/Swagger definitions
"""
from drf_yasg import openapi
from modules.api_messages import Messages

message = Messages()

""" Swagger definitions used in the views_*_.py decorators '@swagger_auto_schema(**object)'. Each parameter is given the
    name of the methods in views_*_.py prepended with 'as_' (auto_schema)
"""

version = openapi.Schema(type=openapi.TYPE_STRING, description='Version number')
slug = openapi.Schema(type=openapi.TYPE_STRING, description='Unique human readable identifier (Slug)')
status = openapi.Schema(type=openapi.TYPE_INTEGER,
                        description='The current state of this module\n\n0: inactive\n1: active')
title = openapi.Schema(type=openapi.TYPE_STRING, description='Descriptive title')
icon = openapi.Schema(type=openapi.TYPE_STRING, description='Icon name')
description = openapi.Schema(type=openapi.TYPE_STRING, description='Description')

modules_for_app = {
    "description": description,
    "slug": slug,
    "title": title,
    "icon": icon,
    "status": status,
    "version": version
}

modules_by_app = {
    "appVersion": version,
    "moduleSlug": slug,
    "moduleVersion": version
}

modules = {
    "slug": slug,
    "title": title,
    "icon": icon,
    "version": version,
    "description": description
}

module_version = {
    "moduleSlug": slug,
    "title": title,
    "icon": icon,
    "version": version,
    "description": description
}

modules_enable = {
    "slug": slug,
    "appVersion": version,
    "moduleVersion": version,
    "status": status
}

module_order = {
    "appVersion": version,
    "order": openapi.Schema(type=openapi.TYPE_ARRAY,
                            items=slug)
}


module_slug_status = {
    "status": status,
    "releases": openapi.Schema(type=openapi.TYPE_ARRAY, items=version)
}

as_module_get = {
    'methods': ['get'],
    'manual_parameters': [
        openapi.Parameter('slug',
                          openapi.IN_QUERY,
                          required=True,
                          description="Slug for requesting modules",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('version',
                          openapi.IN_QUERY,
                          required=True,
                          description="Version for requesting modules",
                          type=openapi.TYPE_STRING)
    ],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties={
                                      'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='result status'),
                                      'result': openapi.Schema(type=openapi.TYPE_OBJECT, properties=modules)
                                  }))
    },
    'tags': ['Module']
}


status_in_releases = {
    'status': openapi.Schema(type=openapi.TYPE_NUMBER, description='status (enum: 0, 1, ...)'),
    'releases': openapi.Schema(type=openapi.TYPE_ARRAY,
                               items=openapi.Schema(type=openapi.TYPE_STRING,
                                                    description='release version (x.y.z)'))
}
module = {
    'slug': openapi.Schema(type=openapi.TYPE_STRING, description='module slug'),
    'status': openapi.Schema(type=openapi.TYPE_NUMBER,
                             description='The status of the module. This allows to deactivate all of its versions '
                                         'in all releases at once.\n\nstatus (enum: 0, 1, ...)'),
}

modules_version_post = {
    'title': openapi.Schema(type=openapi.TYPE_STRING, description='module title'),
    'description': openapi.Schema(type=openapi.TYPE_STRING, description='module description'),
    'version': openapi.Schema(type=openapi.TYPE_STRING, description='module version (x.y.z)'),
    'icon': openapi.Schema(type=openapi.TYPE_STRING, description='icon name')
}

modules_version = {
    'title': openapi.Schema(type=openapi.TYPE_STRING, description='module title'),
    'moduleSlug': openapi.Schema(type=openapi.TYPE_STRING, description='module slug'),
    'description': openapi.Schema(type=openapi.TYPE_STRING, description='module description'),
    'version': openapi.Schema(type=openapi.TYPE_STRING, description='module version (x.y.z)'),
    'icon': openapi.Schema(type=openapi.TYPE_STRING, description='icon name')
}

modules_versions = {
    **modules_version,
    'statusInReleases': openapi.Schema(type=openapi.TYPE_ARRAY,
                                       items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                            properties=status_in_releases))
}

module_in_release = {
    **modules_version,
    'status': openapi.Schema(type=openapi.TYPE_NUMBER, description='status (enum: 0, 1, ...)'),
}

release = {
    'version': openapi.Schema(type=openapi.TYPE_STRING, description='module version (x.y.z)'),
    'releaseNotes': openapi.Schema(type=openapi.TYPE_STRING, description='release notes'),
    'published': openapi.Schema(type=openapi.TYPE_STRING, description='date (YYYY-mm-dd)'),
    'unpublished': openapi.Schema(type=openapi.TYPE_STRING, description='date (YYYY-mm-dd)'),
    'deprecated': openapi.Schema(type=openapi.TYPE_STRING,description='date (YYYY-mm-dd)'),

}

get_release = {
    **release,
    'created': openapi.Schema(type=openapi.FORMAT_DATETIME),
    'modified': openapi.Schema(type=openapi.FORMAT_DATETIME),
    'modules': openapi.Schema(type=openapi.TYPE_ARRAY,
                              items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                   properties=module_in_release)),
    'isDeprecated': openapi.Schema(type=openapi.TYPE_BOOLEAN,description='is the release deprecated?'),
    'isSupported': openapi.Schema(type=openapi.TYPE_BOOLEAN,description='is the release supported?'),
}

post_patch_release = {
    **release,
    'modules': openapi.Schema(type=openapi.TYPE_ARRAY,
                              items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                   properties={
                                                       'moduleSlug': openapi.Schema(type=openapi.TYPE_STRING,
                                                                                    description='module slug'),
                                                       'version': openapi.Schema(type=openapi.TYPE_STRING,
                                                                                 description='module version (x.y.z)'),
                                                       'status': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                                                description='status (enum: 0, 1, ...)')
                                                   }))
}

as_get_release = {
    'methods': ['get'],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties=get_release))
    },
    'tags': ['Release']
}


as_get_releases = {
    'methods': ['get'],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_ARRAY,
                                  items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                       properties=get_release))),
    },
    'tags': ['Releases']
}


as_post_release = {
    'methods': ['post'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=post_patch_release
    ),
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties={
                                      **release,
                                      'created': openapi.Schema(type=openapi.FORMAT_DATETIME),
                                      'modified': openapi.Schema(type=openapi.FORMAT_DATETIME),
                                  })),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        404: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "Module with slug ‘{slug}’ and version ‘{version}’ not found."
                                  }
                              }),
        409: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'message': 'Release version already exists.'
                                  }
                              }),
    },
    'tags': ['Release']
}


as_patch_release = {
    'methods': ['patch'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=post_patch_release
    ),
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties={
                                      **release,
                                      'created': openapi.Schema(type=openapi.FORMAT_DATETIME),
                                      'modified': openapi.Schema(type=openapi.FORMAT_DATETIME),
                                  })),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        404: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "Module with slug ‘{slug}’ and version ‘{version}’ not found."
                                  }
                              }),
        409: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'message': 'Release version already exists.'
                                  }
                              }),
    },
    'tags': ['Release']
}


as_delete_release = {
    'methods': ['delete'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'responses': {
        200: openapi.Response(''),
        403: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'message': 'Release version ‘{version}’ is already published'
                                  }
                              }),
        404: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "Release version ‘{version}’ not found."
                                  }
                              }),
    },
    'tags': ['Release']
}


as_module_version_get = {
    'methods': ['get'],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties=modules_versions))
    },
    'tags': ['Module']

}


as_module_version_post = {
    'methods': ['post'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=modules_version_post
    ),
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties=modules_version)),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        409: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'message': 'Module already exists.'
                                  }
                              }),
    },
    'tags': ['Module']
}


as_module_version_delete = {
    'methods': ['delete'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'responses': {
        200: openapi.Response(''),
        403: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'message': 'Module with slug ‘{slug}’ is being used in a release.'
                                  }
                              }),
        404: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "Module with slug ‘{slug}’ and version ‘{version}’ not found."
                                  }
                              }),
    },
    'tags': ['Module']
}


as_module_version_patch = {
    'methods': ['patch'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=modules_version_post,
    ),
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties=modules_version)),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        409: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'message': 'Module already exists.'
                                  }
                              }),
    },
    'tags': ['Module']

}


as_module_slug_get = {
    'methods': ['get'],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties={
                                      'slug': openapi.Schema(type=openapi.TYPE_STRING, description='slug'),
                                      'status': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                               description='module status (global)'),
                                      'versions': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                 items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                                      properties=modules_versions))
                                  })),
        404: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'status': False,
                                      'id': 'No such slug'
                                  }
                              }),

    },
    'tags': ['Module']
}


as_modules_latest = {
    'methods': ['get'],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_ARRAY,
                                  items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                       properties=module_version)))
    },
    'tags': ['Modules']
}

as_module_slug_status = {
    'methods': ['PATCH'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'request_body': openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Schema(type=openapi.TYPE_OBJECT, properties=module_slug_status)
    ),
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_ARRAY,
                                  items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                       properties=module_slug_status))),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        404: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "Module with slug ‘{slug}’ and version ‘{version}’ not found."
                                  }
                              }),
    },
    'tags': ['Module']
}


as_modules_available_for_release = {
    'methods': ['get'],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                                properties=module_version)))
    },
    'tags': ['Modules']
}


as_module_post = {
    'methods': ['POST'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["slug", "status"],
        properties=module,
    ),
    'responses': {
        200: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'slug': 'string',
                                      'status': 1
                                  }
                              }),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        409: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'message': 'Module already exists.'
                                  }
                              }),
    },
    'tags': ['Module']
}


as_module_patch = {
    'methods': ['PATCH'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["status"],
        properties={
            'status': openapi.Schema(type=openapi.TYPE_NUMBER,
                                     description='The status of the module. This allows to deactivate '
                                                 'all of its versions in all releases at once.\n\n'
                                                 'status (enum: 0, 1, ...)'),
        },
    ),
    'responses': {
        200: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      'slug': 'string',
                                      'status': 1
                                  }
                              }),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        404: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "Module with slug ‘{slug}’ not found."
                                  }
                              }),
    },
    'tags': ['Module']
}


as_module_delete = {
    'methods': ['DELETE'],
    'manual_parameters': [openapi.Parameter('Authorization',
                                            openapi.IN_HEADER,
                                            description="Authorization token",
                                            type=openapi.TYPE_STRING,
                                            required=True)],
    'responses': {
        200: openapi.Response(''),
        400: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "incorrect request body."
                                  }
                              }),
        403: openapi.Response('application/json',
                              examples={
                                  'application/json': {
                                      "message": "Module with slug ‘slug’ is being used in a release."
                                  }
                              }),
    },
    'tags': ['Module']
}

as_modules_for_app_get = {
    'methods': ['get'],
    'manual_parameters': [openapi.Parameter('appVersion',
                                            openapi.IN_HEADER,
                                            description="appVersion for requesting modules",
                                            type=openapi.TYPE_STRING)],
    'responses': {
        200: openapi.Response(
            'application/json',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties={
                                      'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='result status'),
                                      'result': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                               items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                                    properties=modules_for_app))
                                  }))

    },
    'tags': ['Modules for App (legacy app: <= 0.27.0)']
}
