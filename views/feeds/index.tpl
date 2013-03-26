%import time
%from collections import defaultdict
<table id="feeds" class="ink-table ink-hover ink-zebra ink-bordered">
    <thead>
        <tr>
%for h in headers:
%    if 'label' in h:
            <th>{{h['label']}}</th>
%    elif 'icon' in h:
            <th><i class="{{h['icon']}}"></i></th>
%    end
%end
        </tr>
    </thead>
    <tbody>
%for f in feeds:
        <tr>
%    for h in headers:
%        field = h['field']
%        if field in f:
%            value = f[field]
%        elif field in ['manage']:
%            if 'uri' in f:
%                value = '<a href="%s"><i class="%s"></i></a>' % (f['uri'] % f['id'], f['icon'])
%            else:
%                value = ''
%        end
%        if field in ['last_modified','last_checked']:
%            value = time.strftime("%Y-%m-%d",time.localtime(value))
            <td>{{!value}}</td>
%        end
%    end
        </tr>
%end
    </tbody>
</table>
%rebase layout title=title, scripts=[]
