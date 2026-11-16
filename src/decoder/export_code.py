"""Exporta o código final (v5 + 16 densas gaussianas, 16 paridades perfuradas) em texto para o decodificador em C."""
import sys, json
HERE, BG, P = sys.argv[1], sys.argv[2], int(sys.argv[3]); sys.argv = [sys.argv[0], HERE, BG]; sys.path.insert(0, HERE); 
sys.argv = [sys.argv[0], HERE, BG, str(P), "1", "0.1"]
import importlib.util
spec = importlib.util.spec_from_file_location("fair", f"{HERE}/fair.py")
src = open(f"{HERE}/fair.py").read().split("codes = [v5(), fair(), build_5g(K, n, BG)]")[0]
ns = {"__name__": "x"}; exec(compile(src, "fair", "exec"), ns)
c = ns["fair"](); K, n, M = ns["K"], ns["n"], ns["M"]; R = c["R"]; V = len(c["cols"])
with open(f"code_p{P}.txt", "w") as f:
    f.write(f"{V} {K} {R} {n} {len(c['always'])} {M}\n")
    f.write(" ".join(map(str, c["always"])) + "\n"); f.write(" ".join(map(str, c["tx"])) + "\n")
    for v in range(V):
        rows = [r for r in range(R) if (c["cols"][v] >> r) & 1]; f.write(f"{len(rows)} " + " ".join(map(str, rows)) + "\n")
print("exportado", P, "V", V, "K", K, "R", R, "n", n, "densas a partir da equação", M)
