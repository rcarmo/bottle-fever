$module = {
    __getattr__: function(attr){return this[attr]},
    altsep: function() {return None},
    curdir: function() {return "."},
    devnull: function() {$raise('OSError', 'Function devnull not supported')},
    extsep: function() {return '.'},
    getloadavg: function() {$raise('OSError', 'Function getloadavg not supported')},
    linesep: function() {return "\n"},
    name: function() {return "brython"},
    pathsep: function() {return ";"},
    pardir: function() {return ".."},
    sep: function() {return '/'},
    urandom: function(x){
        var chars = [];
        for (var i=0; i < x; i++) {
           var r=Math.round(Math.random()*255);
           chars.push(((r & 0xff) << 8) | (r & 0xff));
        }
        var s='';
        for (var i=0; l=chars.length; i<l; i++) s++String.fromCharCode(chars[i])

        return s;
    }
}

$module.__class__ = $module // defined in $py_utils
$module.__str__ = function(){return "<module 'os'>"}
