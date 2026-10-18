// Supabase Edge Function "redgifs": looks clips up on RedGifs on the page's behalf, because some browsers
// are not allowed to call the RedGifs API directly ("Failed to fetch").
// Deploy with "Verify JWT" turned OFF (the page calls it without a login). It only returns the sound flag,
// size and file addresses of the clips asked for, nothing else.
const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET, OPTIONS',
  'access-control-allow-headers': '*',
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, 'content-type': 'application/json', 'cache-control': 'no-store' } });

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  const ids = (new URL(req.url).searchParams.get('ids') || '').toLowerCase().split(',').map((s) => s.trim()).filter(Boolean);
  if (!ids.length || ids.length > 25 || ids.some((s) => !/^[a-z0-9]{3,64}$/.test(s))) return json({ error: 'bad ids' }, 400);

  // RedGifs ties file addresses to the requesting address and browser, so pass the visitor's through.
  const ip = (req.headers.get('x-forwarded-for') || '').split(',')[0].trim();
  const ua = req.headers.get('user-agent') || 'Mozilla/5.0';
  const base = { 'user-agent': ua, referer: 'https://www.redgifs.com/', origin: 'https://www.redgifs.com' };
  try {
    const a = await fetch('https://api.redgifs.com/v2/auth/temporary', { headers: base });
    if (!a.ok) return json({ error: 'auth ' + a.status }, 502);
    const token = (await a.json()).token;
    if (!token) return json({ error: 'no token' }, 502);
    const q = new URLSearchParams({ ids: ids.join(','), 'user-agent': ua });
    if (ip) q.set('user-addr', ip);
    const r = await fetch(`https://api.redgifs.com/v2/gifs?${q}`, { headers: { ...base, authorization: 'Bearer ' + token } });
    if (!r.ok) return json({ error: 'gifs ' + r.status }, 502);
    const gifs = ((await r.json()).gifs || []).map((g: any) => ({
      id: g.id, hasAudio: !!g.hasAudio, width: g.width || 0, height: g.height || 0,
      urls: { hd: g.urls?.hd, sd: g.urls?.sd, poster: g.urls?.poster, thumbnail: g.urls?.thumbnail },
    }));
    return json({ gifs });
  } catch (e) {
    return json({ error: String(e) }, 502);
  }
});
