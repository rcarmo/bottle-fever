%import logging
%log = logging.getLogger()

%for i in items:
<div class="item vspace">
    <h2>{{!i['title']}}</h2>
    <div class="description">{{!i['html']}}</div>
</div>
%end
%rebase layout title=title, scripts=[]
