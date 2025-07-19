"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.pool = void 0;
exports.initDb = initDb;
const pg_1 = require("pg");
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
exports.pool = new pg_1.Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : undefined
});
async function initDb() {
    const client = await exports.pool.connect();
    try {
        // run schema migrations if not applied
        const schemaSql = fs_1.default.readFileSync(path_1.default.join(__dirname, '../../schema.sql'), 'utf-8');
        await client.query(schemaSql);
        console.log('Database initialized');
    }
    finally {
        client.release();
    }
}
