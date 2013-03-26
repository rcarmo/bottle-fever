$module =  {

    __getattr__ : function(attr){return this[attr]},

    parse : function(json_obj){return JSON.parse(json_obj)},

    stringify : function(obj){return JSON.stringify(obj)},
    
}