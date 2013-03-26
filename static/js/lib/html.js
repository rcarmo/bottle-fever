// creation of an HTML element
$module = (function(){
function $Tag(tagName,args){
    // cl
    var $i = null
    var elt = null
    var elt = $DOMNode(document.createElement(tagName))
    elt.parent = this
    if(args!=undefined && args.length>0){
        $start = 0
        $first = args[0]
        // if first argument is not a keyword, it's the tag content
        if(!isinstance($first,$Kw)){
            $start = 1
            if(isinstance($first,[str,int,float])){
                txt = document.createTextNode($first.toString())
                elt.appendChild(txt)
            } else if(isinstance($first,$TagSum)){
                for($i=0;$i<$first.children.length;$i++){
                    elt.appendChild($first.children[$i])
                }
            } else {
                try{elt.appendChild($first)}
                catch(err){throw ValueError('wrong element '+$first)}
            }
        }
        // attributes
        for($i=$start;$i<args.length;$i++){
            // keyword arguments
            $arg = args[$i]
            if(isinstance($arg,$Kw)){
                if($arg.name.toLowerCase().substr(0,2)==="on"){ // events
                    eval('elt.'+$arg.name.toLowerCase()+'=function(){'+$arg.value+'}')
                }else if($arg.name.toLowerCase()=="style"){
                    elt.set_style($arg.value)
                } else {
                    if($arg.value!==false){
                        // option.selected=false sets it to true :-)
                        try{
                            elt.setAttribute($arg.name.toLowerCase(),$arg.value)
                        }catch(err){
                            throw ValueError("can't set attribute "+$arg.name)
                        }
                    }
                }
            }
        }
    }
    return elt
}

// the classes used for tag sums, $TagSUm and $TagSumClass 
// are defined in py_dom.js

function A(){return $Tag('A',arguments)}

var $src = A+'' // source of function A
// HTML4 tags
$tags = ['A', 'ABBR', 'ACRONYM', 'ADDRESS', 'APPLET',
            'B', 'BDO', 'BIG', 'BLOCKQUOTE', 'BUTTON',
            'CAPTION', 'CENTER', 'CITE', 'CODE',
            'DEL', 'DFN', 'DIR', 'DIV', 'DL',
            'EM', 'FIELDSET', 'FONT', 'FORM', 'FRAMESET',
            'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
            'I', 'IFRAME', 'INS', 'KBD', 'LABEL', 'LEGEND',
            'MAP', 'MENU', 'NOFRAMES', 'NOSCRIPT', 'OBJECT',
            'OL', 'OPTGROUP', 'PRE', 'Q', 'S', 'SAMP',
            'SCRIPT', 'SELECT', 'SMALL', 'SPAN', 'STRIKE',
            'STRONG', 'STYLE', 'SUB', 'SUP', 'TABLE',
            'TEXTAREA', 'TITLE', 'TT', 'U', 'UL',
            'VAR', 'BODY', 'COLGROUP', 'DD', 'DT', 'HEAD',
            'HTML', 'LI', 'P', 'TBODY','OPTION', 
            'TD', 'TFOOT', 'TH', 'THEAD', 'TR',
            'AREA', 'BASE', 'BASEFONT', 'BR', 'COL', 'FRAME',
            'HR', 'IMG', 'INPUT', 'ISINDEX', 'LINK',
            'META', 'PARAM']

// HTML5 tags
$tags = $tags.concat(['ARTICLE','ASIDE','FIGURE','FOOTER','HEADER','NAV',
    'SECTION','AUDIO','VIDEO','CANVAS','COMMAND','DATALIST',
    'DETAILS','OUTPUT','PROGRESS','HGROUP','MARK','METER','TIME',
    'RP','RT','RUBY'])

// create classes
var obj = new Object()
for($i=0;$i<$tags.length;$i++){
    $code = $src.replace(/A/gm,$tags[$i])
    eval("obj."+$tags[$i]+"="+$code)
    eval("obj."+$tags[$i]+'.name="'+$tags[$i]+'"')
}
obj.__getattr__ = function(attr){return this[attr]}
return obj
})()
