$module = {
    __getattr__ : function(attr){return this[attr]},
    random:function(x){return float(Math.random())}
}
$module.__class__ = $module // defined in $py_utils
$module.__str__ = function(){return "<module 'random'>"}