%%
syms s d x n p
f = (1-p)*(d + (n-n*p)*s) / (d + x*s) + 1 / (1+x) - 1;
t = solve(f, x);
t = t(1);
% clear s d x n p f

figure;
hold on;
for d1 = 0.1:0.05:0.4
    ds = d1 * 5000000 / 8;
    ps = 0.1;
    ss = 1514;
    ns = 5:30;

%     v = subs(t, d, ds);
%     v = subs(v, p, ps);
%     v = subs(v, s, ss);
%     v = subs(v, ns);
    v = subs(t, [d, p, s], [ds, ps, ss]);
    v = subs(v, ns);
    plot(ns, vpa(v));
    grid;
end

%% 
syms l r
g = simplify(subs(f, [x, p], [l / (r - l), l/r]))
u = solve(g, l)
u = u(3);

figure;
hold on;
for d1 = 0.1:0.05:0.4
    r = 5000000 / 8;
    d = d1 * r;
    n = 5:30;
    s = 1514;

    v = subs(u);
    plot(n, vpa(v));
    grid;
end

%% 
syms r l d g s x
f = (r-l) * (d + (r-l) * g * s / (l * r) ) - (r-x) * (d + (r-x) * s / (x * r) );
t = solve(f, x);
t = t(2);
% solve(simplify(subs(f, [s,d], [1,0])), x)

figure;
hold on;
for d1 = 0:0.05:0.5
    r = 5000000;
    d = d1;
    l = 0.5 * r;
    s = 1514 * 8;
    g = 2.^(-10:0.1:1);

    v = subs(t);
    plot(g, vpa(v) / r);
    grid;
end

%%
syms r l d g s x
f = (r-l) * ((r-l) * g * s / l) - (r-x) * ((r-x) * s / x);
t = solve(f, x);
t = t(1);
% solve(simplify(subs(f, [s,d], [1,0])), x)

figure;
r = 5000000 / 8;
l = 0.5 * r;
s = 1514 / r;
g = 2.^(-1:0.1:1);

v = subs(t);
plot(g, vpa(v) / r);
grid;

%% 
clearvars;
syms r l d q s x
f = (r-l) * (d + (r-l) / r * q / r ) - (r-x) * (d + (r-x) / x * s / r );
t = solve(f, x);
t = t(2);
% solve(simplify(subs(f, [s,d], [1,0])), x)

figure;
for d1 = 0:0.05:0.5
    r = 5000000;
    d = d1;
    l = 0.1 * r;
    s = 1514 * 8;
    q = s * 2.^(-1:0.1:5);

    v = subs(t);
    semilogx(q/s, vpa(v) / r);
    hold on;
end
grid;


%% 
clearvars;
syms r l d q s x
f = (r-l) * (d + q / r) - (r-x) * (d + 2*s / x);
t = solve(f, x);
t = t(1);
% solve(simplify(subs(f, [s,d], [1,0])), x)

figure;
for d1 = 0.001:0.05:0.5
    r = 5000000;
    d = d1;
    l = 0.5 * r;
    s = 1514 * 8;
    q = s * 2.^(-1:0.1:5);

    v = subs(t);
    plot(q/s, vpa(v)/r);
    hold on;
end
grid;

