import { neon } from '@neondatabase/serverless';
import bcrypt from 'bcryptjs';

const DATABASE_URL = import.meta.env.VITE_DATABASE_URL;

if (!DATABASE_URL) {
    console.error('VITE_DATABASE_URL is not set in environment');
}

const sql = neon(DATABASE_URL || '');

export interface User {
    id: number;
    username: string;
    email: string;
    hashed_password?: string;
    plan?: string;
    video_count?: number;
}

export interface Video {
    id: number;
    title: string;
    r2_key: string;
    url: string;
    user_id: number;
    created_at: string;
}

export interface HistoryItem {
    id: number;
    user_id: number;
    query: string;
    source_url: string | null;
    video_id: number | null;
    video_url?: string;
    created_at: string;
}

// User Actions
export async function getUserByUsername(username: string): Promise<User | null> {
    const result = await sql`
        SELECT id, username, email, hashed_password, plan, video_count
        FROM users
        WHERE username = ${username}
    `;
    return result.length > 0 ? (result[0] as User) : null;
}

export async function createUser(username: string, email: string, passwordPlain: string): Promise<User> {
    // 1. Hash password
    const salt = bcrypt.genSaltSync(10);
    const hash = bcrypt.hashSync(passwordPlain, salt);

    // 2. Insert into DB
    const result = await sql`
        INSERT INTO users (username, email, hashed_password, plan, video_count)
        VALUES (${username}, ${email}, ${hash}, 'free', 0)
        RETURNING id, username, email, plan, video_count
    `;
    return result[0] as User;
}

export async function getVideosByUserId(userId: number): Promise<Video[]> {
    const result = await sql`
        SELECT id, title, r2_key, url, user_id, created_at
        FROM videos
        WHERE user_id = ${userId}
        ORDER BY created_at DESC
    `;
    return result as Video[];
}

export async function getHistoryByUserId(userId: number): Promise<HistoryItem[]> {
    const result = await sql`
        SELECT h.id, h.user_id, h.query, h.source_url, h.video_id, h.created_at, v.url as video_url
        FROM history h
        LEFT JOIN videos v ON h.video_id = v.id
        WHERE h.user_id = ${userId}
        ORDER BY h.created_at DESC
        LIMIT 50
    `;
    return result as HistoryItem[];
}

export async function getAllVideos(): Promise<Video[]> {
    const result = await sql`
        SELECT id, title, r2_key, url, user_id, created_at
        FROM videos
        ORDER BY created_at DESC
        LIMIT 100
    `;
    return result as Video[];
}

// Category Videos Interface
export interface CategoryVideo {
    id: number;
    title: string;
    author: string;
    views: string;
    duration: string;
    image: string;
    category: string;
    url: string;
}

export async function getCategoryVideos(category?: string): Promise<CategoryVideo[]> {
    let query;
    if (category && category !== 'All Videos') {
        query = sql`
            SELECT * FROM category_videos
            WHERE category = ${category}
            ORDER BY id ASC
        `;
    } else {
        query = sql`
            SELECT * FROM category_videos
            ORDER BY id ASC
        `;
    }
    const result = await query;
    return result as CategoryVideo[];
}

export { sql, bcrypt };
