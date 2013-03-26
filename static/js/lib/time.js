$module =  {

    $norm_str: function(arg,nb){
        // left padding with 0
        var res = arg.toString()
        while(res.length<nb){res = '0'+res}
        return res
    },

    __getattr__ : function(attr){return this[attr]},

    clear_interval : function(int_id){window.clearInterval(int_id)},
    
    set_interval : function(func,interval){
        return int(window.setInterval(func,interval))
    },

    set_timeout : function(func,interval){window.setTimeout(func,interval)},

    time : function(){return (new Date()).getTime()},
    
    strftime : function(format,arg){
        var ns = time.$norm_str
        if(arg){var obj = new Date(arg)}else{var obj=new Date()}
        var res = format
        res = res.replace(/%H/,ns(obj.getHours(),2))
        res = res.replace(/%M/,ns(obj.getMinutes(),2))
        res = res.replace(/%S/,ns(obj.getSeconds(),2))
        res = res.replace(/%Y/,ns(obj.getFullYear(),4))
        res = res.replace(/%y/,ns(obj.getFullYear(),4).substr(2))
        res = res.replace(/%m/,ns(obj.getMonth()+1,2))
        res = res.replace(/%d/,ns(obj.getDate(),2))
        return res
    }
}