function dZ(t, e) {
    const n = new Uint32Array(68)
        , i = new Uint32Array(64);
    function r(t, e) {
        const n = 31 & e;
        return t << n | t >>> 32 - n
    }

    function o(t, e) {
        const n = [];
        for (let i = t.length - 1; i >= 0; i--)
            n[i] = 255 & (t[i] ^ e[i]);
        return n
    }

    function s(t) {
        return t ^ r(t, 9) ^ r(t, 17)
    }

    function a(t) {
        let e = 8 * t.length
            , o = e % 512;
        o = o >= 448 ? 512 - o % 448 - 1 : 448 - o - 1;
        const a = new Array((o - 7) / 8)
            , u = new Array(8);
        for (let t = 0, e = a.length; t < e; t++)
            a[t] = 0;
        for (let t = 0, e = u.length; t < e; t++)
            u[t] = 0;
        e = e.toString(2);
        for (let t = 7; t >= 0; t--)
            if (e.length > 8) {
                const n = e.length - 8;
                u[t] = parseInt(e.substr(n), 2),
                    e = e.substr(0, n)
            } else
                e.length > 0 && (u[t] = parseInt(e, 2),
                    e = "");
        const c = new Uint8Array([...t, 128, ...a, ...u])
            , l = new DataView(c.buffer, 0)
            , h = c.length / 64
            , f = new Uint32Array([1937774191, 1226093241, 388252375, 3666478592, 2842636476, 372324522, 3817729613, 2969243214]);
        for (let t = 0; t < h; t++) {
            n.fill(0),
                i.fill(0);
            const e = 16 * t;
            for (let t = 0; t < 16; t++)
                n[t] = l.getUint32(4 * (e + t), !1);
            for (let t = 16; t < 68; t++)
                n[t] = (d = n[t - 16] ^ n[t - 9] ^ r(n[t - 3], 15)) ^ r(d, 15) ^ r(d, 23) ^ r(n[t - 13], 7) ^ n[t - 6];
            for (let t = 0; t < 64; t++)
                i[t] = n[t] ^ n[t + 4];
            const o = 2043430169
                , a = 2055708042;
            let u, c, h, p, v, m = f[0], g = f[1], y = f[2], b = f[3], x = f[4], w = f[5], S = f[6], k = f[7];
            for (let t = 0; t < 64; t++)
                v = t >= 0 && t <= 15 ? o : a,
                    c = (u = r(r(m, 12) + x + r(v, t), 7)) ^ r(m, 12),
                    h = (t >= 0 && t <= 15 ? m ^ g ^ y : m & g | m & y | g & y) + b + c + i[t],
                    p = (t >= 0 && t <= 15 ? x ^ w ^ S : x & w | ~x & S) + k + u + n[t],
                    b = y,
                    y = r(g, 9),
                    g = m,
                    m = h,
                    k = S,
                    S = r(w, 19),
                    w = x,
                    x = s(p);
            f[0] ^= m,
                f[1] ^= g,
                f[2] ^= y,
                f[3] ^= b,
                f[4] ^= x,
                f[5] ^= w,
                f[6] ^= S,
                f[7] ^= k
        }
        var d;
        const p = [];
        for (let t = 0, e = f.length; t < e; t++) {
            const e = f[t];
            p.push((4278190080 & e) >>> 24, (16711680 & e) >>> 16, (65280 & e) >>> 8, 255 & e)
        }
        return p
    }

    const u = 64
        , c = new Uint8Array(u)
        , l = new Uint8Array(u);
    for (let t = 0; t < u; t++)
        c[t] = 54,
            l[t] = 92;
    t.exports = {
        sm3: a,
        hmac: function (t, e) {
            for (e.length > u && (e = a(e)); e.length < u;)
                e.push(0);
            const n = o(e, c)
                , i = o(e, l)
                , r = a([...n, ...t]);
            return a([...i, ...r])
        }
    }

    function o(t) {
        return t.map(t => 1 === (t = t.toString(16)).length ? "0" + t : t).join("")
    }

    return o(a(t))
}

function a(t) {
    const e = [];
    for (let n = 0, i = t.length; n < i; n++) {
        const i = t.codePointAt(n);
        if (i <= 127)
            e.push(i);
        else if (i <= 2047)
            e.push(192 | i >>> 6),
                e.push(128 | 63 & i);
        else if (i <= 55295 || i >= 57344 && i <= 65535)
            e.push(224 | i >>> 12),
                e.push(128 | i >>> 6 & 63),
                e.push(128 | 63 & i);
        else {
            if (!(i >= 65536 && i <= 1114111))
                throw e.push(i),
                    new Error("input is not supported");
            n++,
                e.push(240 | i >>> 18 & 28),
                e.push(128 | i >>> 12 & 63),
                e.push(128 | i >>> 6 & 63),
                e.push(128 | 63 & i)
        }
    }
    return e
}

function TB_BjfbEncrypt(t) {
    return dZ(a(t), '')
}

console.log(TB_BjfbEncrypt(1))
