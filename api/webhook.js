const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');

// Initialize Supabase (Make sure to set these in Vercel Env Variables)
let supabaseUrl = (process.env.SUPABASE_URL || "").trim().replace(/\/$/, "");
const supabaseKey = (process.env.SUPABASE_KEY || "").trim();

if (supabaseUrl && !supabaseUrl.startsWith('https://')) {
    console.error("CRITICAL: SUPABASE_URL must start with https://");
}

const supabase = createClient(supabaseUrl, supabaseKey);

module.exports = async (req, res) => {
    const p = { ...req.query, ...req.body };

    // 1. DATA SAVING SYSTEM
    if (p.action === 'save') {
        if (!p.id || !p.user) return res.status(200).send('missing_fields');
        const { error } = await supabase.from('activations').upsert({ 
            id: p.id, user_id: p.user, username: p.name || 'Unknown', phone: p.phone || 'N/A'
        });
        return res.status(200).send(error ? 'error' : 'saved');
    }

    // 2. FETCH USER ACTIVATIONS
    if (p.action === 'list' && p.user) {
        const { data, error } = await supabase.from('activations').select('*').eq('user_id', p.user).order('created_at', { ascending: false });
        return res.status(200).json(data || []);
    }

    // 3. DELETE ACTIVATION (On Cancel)
    if (p.action === 'delete' && p.id) {
        const { error } = await supabase.from('activations').delete().eq('id', p.id);
        return res.status(200).send('deleted');
    }

    // 4. DELETE ALL ACTIVATIONS FOR USER
    if (p.action === 'delete_all' && p.user) {
        const { error } = await supabase.from('activations').delete().eq('user_id', p.user);
        return res.status(200).send('all_deleted');
    }

    if (req.method === 'GET') {
        return res.status(200).send('💎 ARSMX Webhook with Supabase is active.');
    }

    // 4. WEBHOOK SYSTEM (Incoming SMS)
    const activationId = p.activationId || p.id;
    const code = p.code;
    const service = p.service || 'Unknown';

    if (!activationId || !code) return res.status(200).send('ok'); 

    const token = "8932975551:AAGWLVTDiOeiGHrBJK2ZgZrun2QMCXAdMt8";
    const adminChatId = "974358332"; 

    // Find User ID and Phone from Supabase
    let targetChatId = adminChatId;
    let phoneNumber = "Not Recorded";
    const { data } = await supabase.from('activations').select('user_id, phone').eq('id', activationId).single();
    if (data) {
        if (data.user_id) targetChatId = data.user_id;
        if (data.phone && data.phone !== 'N/A') phoneNumber = data.phone;
    }

    let msg = `💎 <b>ᴀʀsᴍx ᴘʀᴏᴛᴏᴄᴏʟ</b>\n` +
              `📱 <b>ɴᴜᴍʙᴇʀ:</b> <code>+${phoneNumber}</code>\n` +
              `━━━━━━━━━━━━━━━━━━━━\n` +
              `🔢 <b>ᴏᴛᴘ ᴄᴏᴅᴇ:</b>\n` +
              `<blockquote><code>${code}</code></blockquote>\n` +
              `━━━━━━━━━━━━━━━━━━━━\n` +
              `🆔 <b>ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ɪᴅ:</b> <code>${activationId}</code>\n` +
              `📱 <b>sᴇʀᴠɪᴄᴇ:</b> ${service.toUpperCase()}\n` +
              `✅ <b>sᴛᴀᴛᴜs:</b> <code>ᴏᴛᴘ ʀᴇᴄᴇɪᴠᴇᴅ</code>`;

    try {
        await axios.post(`https://api.telegram.org/bot${token}/sendMessage`, { chat_id: targetChatId, text: msg, parse_mode: "HTML" });
        return res.status(200).send('ok');
    } catch (err) {
        return res.status(200).send('ok'); 
    }
};
