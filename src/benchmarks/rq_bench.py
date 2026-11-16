"""RaptorQ (biblioteca Rust via pip 'raptorq'): taxa de sucesso em apagamentos aleatórios e tempo de decodificação, nos mesmos (k, n)."""
import raptorq, os, random, time, json, sys
def trial(pk, e, rng, dec_args, data):
    keep = rng.sample(range(len(pk)), len(pk) - e); dec = raptorq.Decoder.with_defaults(*dec_args); out = None
    for i in keep:
        out = dec.decode(bytes(pk[i]))
        if out is not None: break
    return out == data
res = {}
for (k, n, T, TR) in [(1184, 1480, 64, 3000), (4064, 5080, 64, 1000)]:
    data = os.urandom(k * T); enc = raptorq.Encoder.with_defaults(data, T + 4); pk = enc.get_encoded_packets(n - k); assert len(pk) == n, len(pk)
    rng = random.Random(k)
    for f in (0.15, 0.18, 0.19, 0.195, 0.198, 0.2, 0.202):
        e = round(f * n); ok = sum(trial(pk, e, rng, (len(data), T + 4), data) for _ in range(TR))
        print(f"k={k} n={n} T={T} apagamentos {f:.1%} (e={e}, sobram {n-e-k:+d} acima de k): sucesso {100*ok/TR:.2f}% ({TR} testes)", flush=True)
        res[f"{k}_{f}"] = 100 * ok / TR
for k, n in [(4064, 5080)]:
    T = 1024; data = os.urandom(k * T); enc = raptorq.Encoder.with_defaults(data, T + 4)
    t = time.time(); pk = enc.get_encoded_packets(n - k); te = time.time() - t; rng = random.Random(5)
    for f in (0.0, 0.10, 0.15, 0.19):
        e = round(f * n); ts = []
        for _ in range(15):
            keep = rng.sample(range(n), n - e); dec = raptorq.Decoder.with_defaults(len(data), T + 4); t = time.time(); out = None
            for i in keep:
                out = dec.decode(bytes(pk[i]))
                if out is not None: break
            ts.append(time.time() - t); assert out == data
        print(f"decodificação k={k} T={T}B ({k*T/1e6:.1f} MB), apagamentos {f:.0%}: média {1000*sum(ts)/len(ts):.1f} ms  ({k*T/1e6/(sum(ts)/len(ts)):.0f} MB/s)  [codificação {1000*te:.1f} ms]", flush=True)
