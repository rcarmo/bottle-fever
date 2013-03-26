$module = {
    __getattr__ : function(attr){ return $getattr(this,attr)},
    aceeditor: $AceClass
}

$module.__class__ = $module
$module.__str__ = function() {return "<module 'aceeditor'>"}

$module.__getattr__ = function(attr) {
   return $getattr(this,attr)
}


function $AceClass() { return new $Ace(arguments)}
$AceClass.__class__ = $type
$AceClass.__str__ = function() { return "<class 'ace'>"}

$AceClass.__getattr__ = function(attr) {
   return $getattr(this,attr)
}

/*
//todo: eventually move this function to a "utility" file or use ajax module?
function $get_JS_lib(url,module) {
   var imp=$importer()
   var $xmlhttp=imp[0], fake_qs=imp[1], timer=imp[2], res=null

   $xmlhttp.onreadystatechange = function(){
        if($xmlhttp.readyState==4){
            window.clearTimeout(timer)
            if($xmlhttp.status==200 || $xmlhttp.status==0){res=$xmlhttp.responseText}
            else{
                // don't throw an exception here, it will not be caught (issue #30)
                res = Error()
                res.name = 'NotFoundError'
                res.message = "URL '" + url +"' not found"
            }
        }
   }

   $xmlhttp.open('GET', url,false)
   if('overrideMimeType' in $xmlhttp){$xmlhttp.overrideMimeType("text/plain")}
   $xmlhttp.send()
   if(res.constructor===Error){throw res} // module not found

   try{
      console.log("__BRYTHON__."+ module+"="+res+";")   //module+";")
      eval("__BRYTHON__."+ module+"="+res+";")   //module+";")
   } catch (err) { 
      throw Error("JS Eval Error", "Cannot eval '" + module + "', error:" + err);
   }
}
*/


function $Ace(args) {
    this.__class__ = $AceClass

    //var url="http://d1n0x3qji82z53.cloudfront.net/src-min-noconflict/ace.js"
    //if (__BRYTHON__.aceeditor === undefined) $get_JS_lib(url, 'aceeditor')
 
    this.__getattr__ = function(attr){return this[attr]}

    this.edit= function(id) {
         //this._ace=__BRYTHON.__aceeditor.edit(id); 
         this._ace=ace.edit(id); 
         return this._ace}

    this.getValue= function() {return this._ace.getValue()}

    this.gotoLine= function(linenum) {return this._ace.gotoLine(linenum)}

    this.setTheme= function(theme) {this._ace.setTheme(theme)}
   // this.getSession= function() { return this._ace.getSession()}
    this.setMode= function(mode) {this._ace.getSession().setMode(mode)}
    this.setValue= function(v) {this._ace.setValue(v)}

    this.scrollToRow= function(row) {return this._ace.scrollToRow(row)}

}

