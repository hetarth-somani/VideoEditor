with open('templates/editor.html', 'rb') as f:
    content = f.read()
text = content.decode('utf-8', errors='replace')
lines = text.split('\n')
results = []
for i, line in enumerate(lines):
    l = line.replace('\r','')
    if 'kfApplyToVideo' in l or 'kf-property' in l or 'kf-apply' in l.lower() or 'sa-score' in l or 'saDrawScore' in l:
        results.append('%d: %s' % (i+1, l.strip()[:150]))
with open('kf_search_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))
print('found', len(results))
