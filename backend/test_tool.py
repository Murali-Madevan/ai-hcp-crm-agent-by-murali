"""Test get_hcp_context tool directly."""
import sys, json
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import HCP
from app.agent.tools import build_tools

db = SessionLocal()

# Test direct query
for name in ['Dr. Mehta', 'Mehta', 'Anjali', 'Dr. Anjali Mehta']:
    hcp = db.query(HCP).filter(HCP.name.ilike(f'%{name}%')).first()
    print(f'Direct query with "{name}": {hcp.name if hcp else "NOT FOUND"}')

# Test the actual tool
tools = {t.name: t for t in build_tools(db)}
tool = tools['get_hcp_context']

for name in ['Dr. Mehta', 'Mehta', 'Anjali', 'Dr. Anjali Mehta']:
    print(f'\nTool invoke with hcp_name="{name}":')
    result = json.loads(tool.invoke({'hcp_name': name}))
    if 'error' in result:
        print(f'  ERROR: {result["error"]}')
    else:
        print(f'  Found: {result["name"]} ({result["specialty"]})')

db.close()
