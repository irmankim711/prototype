"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const helmet_1 = __importDefault(require("helmet"));
const cors_1 = __importDefault(require("cors"));
const morgan_1 = __importDefault(require("morgan"));
const cookie_parser_1 = __importDefault(require("cookie-parser"));
const dotenv_1 = __importDefault(require("dotenv"));
const rateLimiter_1 = __importDefault(require("./middleware/rateLimiter"));
const auth_1 = __importDefault(require("./routes/auth"));
const dashboard_1 = __importDefault(require("./routes/dashboard"));
const db_1 = require("./utils/db");
dotenv_1.default.config();
const PORT = process.env.PORT || 5000;
async function bootstrap() {
    await (0, db_1.initDb)();
    const app = (0, express_1.default)();
    app.use((0, helmet_1.default)());
    app.use((0, cors_1.default)({ origin: process.env.CORS_ORIGIN || '*', credentials: true }));
    app.use((0, cookie_parser_1.default)());
    app.use(express_1.default.json());
    app.use(rateLimiter_1.default);
    app.use((0, morgan_1.default)('combined'));
    app.get('/health', (_, res) => res.json({ status: 'OK' }));
    app.use('/api/auth', auth_1.default);
    app.use('/api/dashboard', dashboard_1.default);
    app.use((err, _req, res, _next) => {
        console.error(err);
        res.status(err.status || 500).json({ error: err.message || 'Internal Server Error' });
    });
    app.listen(PORT, () => {
        console.log(`Auth server running on port ${PORT}`);
    });
}
bootstrap().catch((err) => {
    console.error('Failed to bootstrap server', err);
    process.exit(1);
});
