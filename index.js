const axios = require('axios');

module.exports = async (req, res) => {
    const p = req.body || req.query || {};
    const activationId = p.activationId || p.id;
    const code = p.code || 'N/A';
    
    // Test response for GET requests
    if (req.method === 'GET') {
        return res.status(200).send('API is Online! Last Webhook ID: ' + activationId);
    }

    const token = "8932975551:AAGWLVTDiOeiGHrBJK2ZgZrun2QMCXAdMt8";
    const adminChatId = "974358332"; 

    try {
        await axios.post(`https://api.telegram.org/bot${token}/sendMessage`, {
            chat_id: adminChatId,
            text: `💎 *ARSMX Webhook*\n🆔 ID: ${activationId}\n🔢 Code: \`${code}\`\n📦 Data: \`${JSON.stringify(p)}\``,
            parse_mode: "Markdown"
        });
        return res.status(200).send('ok');
    } catch (error) {
        return res.status(200).send('ok');
    }
};
