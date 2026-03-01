const fs = require('fs');
const file = 'frontend/src/contexts/LiveAPIContext.tsx';
let content = fs.readFileSync(file, 'utf8');

content = content.replace(/import type \{ ServerMessage \} from '\.\.\/types\/websocket';/, '// import type { ServerMessage } from \'../types/websocket\';');

fs.writeFileSync(file, content);
