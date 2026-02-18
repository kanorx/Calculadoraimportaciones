def calc_avion(p_u, trm, q, f_u, ar, iv, adm, p_v, c_ml):
    base_cop = (p_u * trm * q) + (f_u * trm)
    c_tot = (base_cop * (1 + ar) * (1 + iv)) + adm
    c_u = c_tot / q if q > 0 else 0
    i_n = p_v * (1 - c_ml)
    viab = i_n / c_u if c_u > 0 else 0
    return {"costo_total": c_tot, "unitario": c_u, "ingreso_neto": i_n, "viabilidad": viab}

def calc_barco(p_u, trm, q, env, tc, alt, anc, lar, caj, cbm_v, fn, p_v, c_ml):
    base_cop = ((p_u * q) + env) * trm * (1 + tc)
    vol = (alt * anc * lar / 1000000) * caj
    c_nac = vol * cbm_v
    c_tot = base_cop + c_nac + fn
    c_u = c_tot / q if q > 0 else 0
    i_n = p_v * (1 - c_ml)
    viab = i_n / c_u if c_u > 0 else 0
    return {"costo_total": c_tot, "costo_cbm": c_nac, "volumen": vol, "unitario": c_u, "ingreso_neto": i_n, "viabilidad": viab}
