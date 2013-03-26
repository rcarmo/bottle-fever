<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title>{{title}}</title>
        <link rel="stylesheet" href="css/ink-min.css">
        <link rel="stylesheet" href="css/main.css">
        <script src="js/brython.js"></script>
%if defined('scripts'):
    %for script in scripts:    
        <script src="js/{{script}}"></script>
    %end
%end
    </head>
    <body onload="brython()">
        <nav class="ink-navigation">
            <ul class="menu horizontal black">
                <li><a href="#">bottle-fever</a></li>
            </ul>
        </nav>
        <div id="main" class="ink-grid vspace">
            %include
        </div>
    </body>
</html>
