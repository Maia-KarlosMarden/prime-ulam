import raptorq, os, random, time, sys
def run(k, n, T, trials, fracs):
    data = os.urandom(k * T); enc = raptorq.Encoder.with_defaults(data, T + 4); pk = enc.get_encoded_packets(n - k); assert len(pk) == n
    pk = [bytes(p) for p in pk]; rng = random.Random(7)
    print(f"RaptorQ k={k} n={n} T={T} B (bloco {k*T/1e6:.2f} MB)")
    for f in fracs:
        e = round(f * n); ts = []; ov = []; ok = 0
        for _ in range(trials):
            keep = rng.sample(range(n), n - e)
            t0 = time.perf_counter()
            for i in keep: b = pk[i]            # sobrecarga do laço em Python, sem decodificar
            ov.append(time.perf_counter() - t0)
            dec = raptorq.Decoder.with_defaults(len(data), T + 4); out = None; t0 = time.perf_counter()
            for i in keep:
                out = dec.decode(pk[i])
                if out is not None: break
            ts.append(time.perf_counter() - t0); ok += out == data
        m = sum(ts) / trials; o = sum(ov) / trials
        print(f"  perda {f:5.1%} (e={e:4d}): sucesso {ok}/{trials}  tempo médio {1000*m:.2f} ms (laço Python ~{1000*o:.2f} ms)  = {k*T/1e6/m:.0f} MB/s medido, ~{k*T/1e6/max(m-o,1e-9):.0f} MB/s descontando o laço", flush=True)
run(1184, 1480, 1024, 100, (0.10, 0.15, 0.17, 0.19))
run(4064, 5080, 1024, 50, (0.10, 0.15, 0.17, 0.19))
