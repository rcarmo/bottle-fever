<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{{title}}</title>
    <link rel="stylesheet" href="/css/docs.css">
    <script src="/js/lib/zepto.min.js"></script>
    <script src="/js/lib/marked.js"></script>

    <script>
        $(document).ready(function () { 
            $('.docstring').each(function() {
                $(this).html(marked($(this).text()))
            })
        });
    </script>
  </head>
  <body>

  <h1 class="title">{{title}}</h1>

  <div class="content">
<ul class="list">
%for item in docs:
<li>
    <h1>{{item['function'].title().replace('_',' ')}}</h1>
    <h2>{{item['method']}} {{item['route']}}</h2>
    <div class="docstring">{{item['doc']}}</div>
</li>
%end
</ul>
  </div>
  </body>
</html>
