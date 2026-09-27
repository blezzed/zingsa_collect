from pathlib import Path
token = 'f3637cb841535f40823ed8b28e22dd364579e4840503b60cfada955ef12f6e19'
p = Path('/home/zingsa/Documents/zingsa_collect/.env')
text = p.read_text()
import re
if re.search(r'^MAINTENANCE_OWNER_TOKEN=', text, flags=re.M):
    text = re.sub(r'^MAINTENANCE_OWNER_TOKEN=.*$', f'MAINTENANCE_OWNER_TOKEN={token}', text, flags=re.M)
else:
    text += f'\nMAINTENANCE_OWNER_TOKEN={token}\n'
p.write_text(text)
print('token_set')
