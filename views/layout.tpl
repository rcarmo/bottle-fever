<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title>{{title}}</title>
        <link rel="stylesheet" href="css/ink-min.css">
        <script src="js/brython.js"></script>
%if defined('scripts'):
    %for script in scripts:    
        <script src="js/{{script}}"></script>
    %end
%end
    </head>
    <body>
        <nav class="ink-navigation">
            <ul class="menu horizontal black">
                <li>bottle-fever</li>
            </ul>
        </nav>
        <div id="main" class="ink-grid">
            %include
        </div>
    </body>
</html>
