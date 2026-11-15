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
    if (!a.ok) return json({ error: 'auth ' + a.status + ' ' + (await a.text()).slice(0, 120) }, 502);
    const token = (await a.json()).token;
    if (!token) return json({ error: 'no token' }, 502);
    const q = new URLSearchParams({ 'user-agent': ua });
    if (ip) q.set('user-addr', ip);
    const auth = { ...base, authorization: 'Bearer ' + token };
    const shape = (g: any) => ({
      id: g.id, hasAudio: !!g.hasAudio, width: g.width || 0, height: g.height || 0, duration: g.duration || 0,
      urls: { hd: g.urls?.hd, sd: g.urls?.sd, poster: g.urls?.poster, thumbnail: g.urls?.thumbnail },
    });
    const list = async (qs: string) => fetch(`https://api.redgifs.com/v2/gifs?ids=${ids.join(',')}${qs}`, { headers: auth });
    let r = await list('&' + q);
    // If the list is refused with the visitor's address and browser attached, try once without them (RedGifs has changed what it accepts before).
    let qs = '?' + q;
    if (r.status === 404) { const r2 = await list(''); if (r2.ok) { r = r2; qs = ''; } }
    if (r.ok) return json({ v: 2, gifs: ((await r.json()).gifs || []).map(shape) });
    if (r.status !== 404) return json({ error: 'gifs ' + r.status + ' ' + (await r.text()).slice(0, 120) }, 502);
    // RedGifs refuses the whole list (404) when one clip in it no longer exists: ask for each clip on its own instead, a few at a time.
    const gifs: any[] = [], missing: string[] = []; let other = '';
    const one = async (id: string, qq: string) => fetch(`https://api.redgifs.com/v2/gifs/${id}${qq}`, { headers: auth });
    for (let i = 0; i < ids.length; i += 5) {
      await Promise.all(ids.slice(i, i + 5).map(async (id) => {
        let o = await one(id, qs);
        if (o.status === 404 && qs) o = await one(id, '');
        if (o.ok) { const g = (await o.json()).gif; if (g) gifs.push(shape(g)); else missing.push(id); }
        else if (o.status === 404 || o.status === 410) missing.push(id);
        else other = other || ('gif ' + o.status + ' ' + (await o.text()).slice(0, 80));
      }));
    }
    if (!gifs.length) return json({ error: other || ('gifs 404 (all ' + ids.length + ' refused, one by one too)') }, 502);
    return json({ v: 2, gifs, missing });
  } catch (e) {
    return json({ error: String(e) }, 502);
  }
});
