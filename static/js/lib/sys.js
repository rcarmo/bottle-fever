$module = {
    __getattr__ : function(attr){
        if(attr==="stdout"){return document.$stdout}
        if(attr==="stderr"){return document.$stderr}
        else{return $getattr(this,attr)}
        },
    __setattr__ : function(attr,value){
        if(attr==="stdout"){document.$stdout=value}
        if(attr==="stderr"){document.$stderr=value}
        },
    has_local_storage:__BRYTHON__.has_local_storage,
    has_json:__BRYTHON__.has_json,
    version_info:__BRYTHON__.version_info,
    path:__BRYTHON__.path
}
