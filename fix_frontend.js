const fs = require('fs');
const file = 'frontend/src/contexts/LiveAPIContext.tsx';
let content = fs.readFileSync(file, 'utf8');

content = content.replace(/import \{ LiveConfig, ServerMessage \} from/, 'import { LiveConfig } from');

fs.writeFileSync(file, content);
