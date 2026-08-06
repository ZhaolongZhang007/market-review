const colors = {
  text: "#a0a0a0",
  textLight: "#ffffff",
  grid: "rgba(255,255,255,0.05)",
  accent: "#1677ff",
  up: "#ff4d4f",
  down: "#52c41a",
  orange: "#fa8c16"
};

const placeholderWords = ["交易日" + "刷新", "刷新", "接入"].map((word) => `待${word}`);

const fallbackThemes = [
  {
    title: "风险主线",
    summary: "高位题材和小盘方向更容易受情绪扰动，先控制回撤。",
    tags: ["高位回撤", "小盘波动", "缩量谨慎"],
    color: "var(--up)"
  },
  {
    title: "逆势主线",
    summary: "优先观察资金连续流入且有基本面催化的方向。",
    tags: ["AI算力", "创新药", "政策催化"],
    color: "var(--accent-light)"
  },
  {
    title: "防御主线",
    summary: "指数震荡阶段，红利、权重和现金流稳定资产适合作为底仓观察。",
    tags: ["高股息", "权重托底", "低波动"],
    color: "var(--orange)"
  }
];

// 大师展示元数据（头像/分类/图标）。观点正文一律来自 insights.json，
// 不在此处保留任何预置文案，避免过期观点被当成当日结论。
const masters = [
  {
    "category": "价值投资",
    "icon": "fa-gem",
    "name": "沃伦·巴菲特",
    "avatar": "巴",
    "avatarStyle": "linear-gradient(135deg, #f6d365, #fda085)"
  },
  {
    "category": "情绪流",
    "icon": "fa-theater-masks",
    "name": "炒股养家",
    "avatar": "养",
    "avatarStyle": "linear-gradient(135deg, #667eea, #764ba2)"
  },
  {
    "category": "龙头战法",
    "icon": "fa-crown",
    "name": "赵老哥",
    "avatar": "赵",
    "avatarStyle": "linear-gradient(135deg, #ffecd2, #fcb69f)"
  },
  {
    "category": "趋势交易",
    "icon": "fa-chart-line",
    "name": "杰西·利弗莫尔",
    "avatar": "利",
    "avatarStyle": "linear-gradient(135deg, #4facfe, #00f2fe)"
  },
  {
    "category": "成长投资",
    "icon": "fa-seedling",
    "name": "彼得·林奇",
    "avatar": "林",
    "avatarStyle": "linear-gradient(135deg, #43e97b, #38f9d7)"
  },
  {
    "category": "价值成长",
    "icon": "fa-compass",
    "name": "查理·芒格",
    "avatar": "芒",
    "avatarStyle": "linear-gradient(135deg, #f093fb, #f5576c)"
  },
  {
    "category": "宏观配置",
    "icon": "fa-globe",
    "name": "霍华德·马克斯",
    "avatar": "马",
    "avatarStyle": "linear-gradient(135deg, #fa709a, #fee140)"
  },
  {
    "category": "量化趋势",
    "icon": "fa-wave-square",
    "name": "詹姆斯·西蒙斯",
    "avatar": "西",
    "avatarStyle": "linear-gradient(135deg, #30cfd0, #330867)"
  },
  {
    "category": "短线情绪",
    "icon": "fa-bolt",
    "name": "作手新一",
    "avatar": "新",
    "avatarStyle": "linear-gradient(135deg, #667eea, #764ba2)"
  },
  {
    "category": "龙头战法",
    "icon": "fa-crown",
    "name": "乔帮主",
    "avatar": "乔",
    "avatarStyle": "linear-gradient(135deg, #ff9a9e, #fecfef)"
  },
  {
    "category": "弱转强",
    "icon": "fa-rotate",
    "name": "退学炒股",
    "avatar": "退",
    "avatarStyle": "linear-gradient(135deg, #a8edea, #fed6e3)"
  },
  {
    "category": "打板高频",
    "icon": "fa-fire",
    "name": "北京炒家",
    "avatar": "北",
    "avatarStyle": "linear-gradient(135deg, #43e97b, #38f9d7)"
  },
  {
    "category": "情绪周期",
    "icon": "fa-temperature-half",
    "name": "涅槃重生",
    "avatar": "涅",
    "avatarStyle": "linear-gradient(135deg, #ffecd2, #fcb69f)"
  },
  {
    "category": "价值防守",
    "icon": "fa-shield-halved",
    "name": "邓普顿",
    "avatar": "邓",
    "avatarStyle": "linear-gradient(135deg, #89f7fe, #66a6ff)"
  },
  {
    "category": "成长质量",
    "icon": "fa-medal",
    "name": "菲利普·费雪",
    "avatar": "费",
    "avatarStyle": "linear-gradient(135deg, #d4fc79, #96e6a1)"
  },
  {
    "category": "价格行为",
    "icon": "fa-chart-simple",
    "name": "斯坦·温斯坦",
    "avatar": "温",
    "avatarStyle": "linear-gradient(135deg, #c471f5, #fa71cd)"
  },
  {
    "category": "逆向投资",
    "icon": "fa-arrows-turn-to-dots",
    "name": "约翰·聂夫",
    "avatar": "聂",
    "avatarStyle": "linear-gradient(135deg, #fddb92, #d1fdff)"
  },
  {
    "category": "产业趋势",
    "icon": "fa-microchip",
    "name": "凯茜·伍德",
    "avatar": "木",
    "avatarStyle": "linear-gradient(135deg, #84fab0, #8fd3f4)"
  }
];

const risks = [
  {
    icon: "fa-microchip",
    tone: "red",
    title: "海外科技波动",
    desc: "美股科技链条波动可能传导至 A 股半导体、AI硬件和电子材料。"
  },
  {
    icon: "fa-chart-line",
    tone: "orange",
    title: "题材分化",
    desc: "指数上涨不等于个股普涨，关注上涨家数、跌停家数与成交额能否同步改善。"
  },
  {
    icon: "fa-coins",
    tone: "yellow",
    title: "流动性风险",
    desc: "缩量环境下小盘股和高位股承接更脆弱，仓位不宜过度前置。"
  }
];

const strategyItems = [
  ["选股核心", "主要策略是买入趋势强势股：行业有强度、个股有成交、均线多头、回踩不破。", ""],
  ["买点纪律", "优先买分歧后的转强、突破后的回踩确认、放量新高后的首次缩量整理。", "cyan"],
  ["仓位管理", "激进型控制在三成以内，稳健型以两成观察仓为主，保守型等待放量确认。", "pink"],
  ["卖出纪律", "放量跌破 5 日线、跌破平台下沿、板块核心股转弱时先降仓。", ""]
];

const checklist = [
  ["趋势", "股价在 5/10/20 日线上方，均线向上发散", true],
  ["强度", "所属热点板块强度排序靠前，且有核心个股带动", true],
  ["量能", "突破或转强当天明显放量，回踩时缩量", false],
  ["位置", "不追连续加速后的缩量一致，等分歧承接", false],
  ["风险", "跌破关键均线或板块资金流出时及时降仓", false]
];

let chartInstances = [];

function $(selector) {
  return document.querySelector(selector);
}

function safe(value, fallback = "--") {
  return value === undefined || value === null || value === "" ? fallback : String(value);
}

function isPlaceholder(value) {
  const text = safe(value, "").trim();
  return !text || text === "--" || placeholderWords.some((word) => text.includes(word));
}

function recentText(value, fallback = "最近收盘样本") {
  return isPlaceholder(value) ? fallback : safe(value, fallback);
}

function escapeHtml(value, fallback = "--") {
  return recentText(value, fallback)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeUrl(value) {
  const url = safe(value, "");
  return /^https?:\/\//.test(url) ? url.replaceAll('"', "%22") : "";
}

function sanitizePlaceholders(value) {
  if (Array.isArray(value)) return value.map(sanitizePlaceholders);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, sanitizePlaceholders(item)]));
  }
  if (typeof value !== "string") return value;
  return placeholderWords.reduce((text, word) => text.replaceAll(word, "最近收盘样本"), value);
}

// Defense-in-depth against a dirty market.json: an index can't trade at 0 and
// can't move ±100% in a session. Scrub such entries to "--" so heroSubtitle,
// getTemperature, deriveStyleRows and renderIndices never surface -100% garbage
// even if the data layer's guards were bypassed (old file, manual edit).
// 单一的 30% 阈值通吃三种量纲完全不同的标的，结果放过了「韩国KOSPI +17.91%」
// ——主要指数单日涨 18% 在历史上近乎不可能，但 17.91 < 30 就漏过去了。
// 按品种分级：宽基指数（A股与海外）现实上限约 12%，汇率约 3%。
const MOVE_LIMITS = { index: 12, fx: 3 };

function moveLimitFor(name = "") {
  return /人民币|汇率|USD|CNH|CNY/i.test(String(name)) ? MOVE_LIMITS.fx : MOVE_LIMITS.index;
}

function isSaneIndex(item = {}) {
  const value = Number(item.value);
  const change = Number(item.changePercent);
  if (Number.isFinite(value) && value <= 0) return false;
  if (Number.isFinite(change) && Math.abs(change) >= moveLimitFor(item.name)) return false;
  return true;
}

function sanitizeIndices(indices) {
  if (!Array.isArray(indices)) return indices;
  return indices.map((item) => {
    if (isSaneIndex(item)) return item;
    return {
      ...item,
      value: null,
      valueText: "--",
      changePercent: null,
      changeText: "--",
      sparkline: [],
      dirty: true
    };
  });
}

function tone(value) {
  if (Number(value) > 0) return "up";
  if (Number(value) < 0) return "down";
  return "flat";
}

function arrowIcon(value) {
  if (Number(value) > 0) return "fa-arrow-up";
  if (Number(value) < 0) return "fa-arrow-down";
  return "fa-minus";
}

function toNumber(value) {
  if (typeof value === "number") return value;
  const match = safe(value, "").replaceAll(",", "").match(/-?\d+(\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

// 所有"选最大值 / 求平均"的推导都必须排除 stale 和 dirty，否则会出现
// 页面顶部黄条刚说"中证2000 未取到最新值"，两屏之后驾驶舱头条就写
// "进攻模式：中证2000 +3.20%" 的情况——引用的正是刚被标为不可信的那个数。
function isUsableIndex(item = {}) {
  return Number.isFinite(item.changePercent) && !item.stale && !item.dirty;
}

function getTopIndex(indices = []) {
  const usable = [...indices].filter(isUsableIndex);
  // 全都不可用时宁可返回空（下游有 safe(topIndex.name, "核心指数") 兜底），
  // 也不要拿一个已知不可信的数去当头条。
  return usable.sort((a, b) => b.changePercent - a.changePercent)[0] || {};
}

function getTopSector(sectors = []) {
  return [...sectors]
    .sort((a, b) => (Number(b.strength) || 0) - (Number(a.strength) || 0))[0] || {};
}

function deriveStyleRows(market = {}) {
  const indices = market.indices || [];
  const large = avgChange(indices, ["上证50", "沪深300", "上证指数"]);
  const small = avgChange(indices, ["中证2000", "中证500", "微盘股"]);
  const growth = avgChange(indices, ["科创50", "创业板50", "中证2000"]);
  const value = avgChange(indices, ["上证50", "沪深300"]);
  const tech = avgChange(indices, ["科创50", "创业板50"]);
  const dividend = avgChange(indices, ["上证50"]);

  const derived = [
    {
      label: "大盘 / 小票",
      value: large !== null && small !== null ? (large >= small ? "大盘占优" : "小票占优") : "待确认",
      score: scoreFromDiff((large ?? 0) - (small ?? 0)),
      left: "小票",
      right: "大盘"
    },
    {
      label: "价值 / 成长",
      value: value !== null && growth !== null ? (value >= growth ? "价值占优" : "成长占优") : "待确认",
      score: scoreFromDiff((value ?? 0) - (growth ?? 0)),
      left: "成长",
      right: "价值"
    },
    {
      label: "红利 / 科技",
      value: dividend !== null && tech !== null ? (dividend >= tech ? "红利占优" : "科技占优") : "待确认",
      score: scoreFromDiff((dividend ?? 0) - (tech ?? 0)),
      left: "科技",
      right: "红利"
    }
  ];

  return (market.styleMatrix && market.styleMatrix.length ? market.styleMatrix : derived)
    .map((item, index) => ({ ...derived[index], ...item }));
}

async function readJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json();
}

// insights.json is produced by the chat round-trip and may legitimately not
// exist yet — the dashboard must still render its factual half.
async function readJsonOptional(path) {
  try {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

function insightsFromStorage() {
  try {
    const raw = localStorage.getItem("marketInsights");
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

function emptyState(message, hint) {
  return `
    <div class="empty-state">
      <i class="fas fa-circle-info"></i>
      <div class="empty-state-text">${escapeHtml(message)}</div>
      ${hint ? `<div class="empty-state-hint">${escapeHtml(hint)}</div>` : ""}
    </div>
  `;
}

const INSIGHTS_HINT = "运行 python3 make_prompt.py，把 prompt 贴进 chat，再用「洞察」面板粘回结果。";

function commonChartOption() {
  return {
    backgroundColor: "transparent",
    textStyle: { fontFamily: "Inter, sans-serif" },
    tooltip: {
      backgroundColor: "#141414",
      borderColor: "rgba(255,255,255,0.08)",
      borderWidth: 1,
      textStyle: { color: "#e0e0e0", fontSize: 12 },
      extraCssText: "box-shadow: 0 4px 12px rgba(0,0,0,0.5); border-radius: 8px;"
    }
  };
}

function renderSparkline(element, data, lineColor) {
  if (!window.echarts || !element) return;
  const values = Array.isArray(data) ? data : [];
  // 以前这里在没数据时填 [100,100,100,100]，画出一条平线——看起来像"走势平稳"，
  // 实际是无数据。宁可留白并写明，也不要画一条假曲线。
  if (values.length < 2) {
    element.innerHTML = `<div class="sparkline-empty">走势数据缺失</div>`;
    return;
  }
  element.innerHTML = "";
  const chart = echarts.init(element);
  chart.setOption({
    ...commonChartOption(),
    grid: { left: 0, right: 0, top: 2, bottom: 2 },
    xAxis: { show: false, type: "category", data: values.map((_, index) => index) },
    yAxis: { show: false, type: "value", scale: true },
    series: [{
      type: "line",
      data: values,
      smooth: true,
      symbol: "none",
      lineStyle: { width: 2, color: lineColor },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${lineColor}33` },
            { offset: 1, color: `${lineColor}05` }
          ]
        }
      }
    }]
  });
  chartInstances.push(chart);
}

function renderHero(market) {
  const status = safe(market.marketStatus);
  $("#navStatus").textContent = status;
  $("#navStatus").classList.toggle("closed", status !== "交易中");
  $("#navDate").textContent = safe(market.tradingDate);
  $("#heroDate").textContent = safe(market.tradingDateText);
  $("#heroTurnover").textContent = `成交 ${safe(market.turnoverText)}`;
  $("#heroUpdated").textContent = `更新 ${safe(market.updatedAtText)}`;

  const leaders = [...(market.indices || [])]
    .filter((item) => Number.isFinite(item.changePercent))
    .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
    .slice(0, 3)
    .map((item) => `${item.name}${item.changeText}`)
    .join("，");
  $("#heroSubtitle").textContent = leaders
    ? `${leaders}。结合全球市场和新闻催化，判断今日风险偏好。`
    : "每日深度复盘，助你洞察市场先机";
}

function getTemperature(market = {}) {
  const sentiment = market.sentiment || {};
  const upCount = toNumber(sentiment.upCount);
  const downCount = toNumber(sentiment.downCount);
  const limitUp = toNumber(sentiment.limitUp);
  const limitDown = toNumber(sentiment.limitDown);
  const breakRate = toNumber(sentiment.breakRate);
  const avgIndex = avgChange(market.indices || [], ["上证指数", "沪深300", "创业板50", "科创50"]);

  let score = 50;
  if (upCount !== null && downCount !== null && upCount + downCount > 0) {
    score += ((upCount / (upCount + downCount)) - 0.5) * 34;
  }
  if (limitUp !== null) score += Math.min(limitUp, 90) * 0.16;
  if (limitDown !== null) score -= Math.min(limitDown, 60) * 0.28;
  if (breakRate !== null) score -= Math.min(breakRate, 80) * 0.12;
  if (avgIndex !== null) score += avgIndex * 5;

  const value = Math.round(clamp(score, 8, 92));
  const label = value >= 78 ? "亢奋" : value >= 64 ? "活跃" : value >= 48 ? "修复" : value >= 32 ? "谨慎" : "冰点";
  return { value, label, upCount, downCount, limitUp, limitDown, breakRate };
}

function temperatureLabel(value) {
  const score = Number(value);
  if (score >= 78) return "亢奋";
  if (score >= 64) return "活跃";
  if (score >= 48) return "修复";
  if (score >= 32) return "谨慎";
  return "冰点";
}

// 这段解读原本后半句写死「仍处在试探修复阶段…升级到活跃」，于是 5 档标签里
// 有 4 档会自相矛盾——今天标签是「亢奋」，解读却说还在修复、还没到活跃。
const TEMPERATURE_BRIEFS = {
  亢奋: "情绪已在高位，赚钱效应集中但分歧随时放大。若涨停生态转弱或炸板率抬升，温度会从「亢奋」回落到「活跃」。",
  活跃: "赚钱效应已经确立。若涨跌家数和涨停生态继续走强，温度才会从「活跃」升级到「亢奋」。",
  修复: "市场仍处在试探修复阶段。若涨跌家数和涨停生态同步改善，温度才会从「修复」升级到「活跃」。",
  谨慎: "做多情绪偏弱、试错成本高。需先看到涨跌家数和涨停生态回暖，温度才会从「谨慎」回到「修复」。",
  冰点: "情绪处于极端低位，超跌反弹前不宜主动进攻。需等涨跌家数和涨停生态止跌，温度才会从「冰点」回到「谨慎」。"
};

function temperatureBrief(label) {
  const body = TEMPERATURE_BRIEFS[label] || "关注涨跌家数与涨停生态的边际变化。";
  return `${label}区间，${body}`;
}

function temperatureTone(value) {
  const score = Number(value);
  if (score >= 78) return "hot";
  if (score >= 64) return "warm";
  if (score >= 48) return "repair";
  if (score >= 32) return "cool";
  return "ice";
}

function fallbackTemperatureHistory(current) {
  // No real history yet (first run). Show only today rather than a fabricated
  // month — the backend accumulates real points from here on.
  return [{ label: "今日", value: current.value, tag: "今日" }];
}

function renderTemperatureHistory(sentiment = {}, current) {
  const history = (Array.isArray(sentiment.history) && sentiment.history.length ? sentiment.history : fallbackTemperatureHistory(current))
    .map((item) => {
      const value = clamp(toNumber(item.value) ?? current.value, 8, 92);
      return {
        label: safe(item.label || item.date, "--"),
        value,
        tag: safe(item.tag, temperatureLabel(value)),
        note: safe(item.note, "")
      };
    })
    .slice(-24);

  if (!history.length) return;

  const minItem = history.reduce((min, item) => item.value < min.value ? item : min, history[0]);
  const maxItem = history.reduce((max, item) => item.value > max.value ? item : max, history[0]);
  const today = history[history.length - 1];
  const avg = Math.round(history.reduce((sum, item) => sum + item.value, 0) / history.length);
  const iceCount = history.filter((item) => item.value < 32).length;

  $("#temperatureHistory").innerHTML = `
    <div class="temperature-history-head">
      <div>
        <strong>近一月情绪温度</strong>
        <span>今日 ${today.value} · ${temperatureLabel(today.value)}，月均 ${avg}</span>
      </div>
      <em>${iceCount ? `${iceCount}次冰点` : "未现冰点"}</em>
    </div>
    <div class="temperature-zones" aria-hidden="true">
      <span>冰点</span><span>谨慎</span><span>修复</span><span>活跃</span><span>亢奋</span>
    </div>
    <div class="temperature-history-bars">
      ${history.map((item) => {
        const isToday = item === today;
        const isExtreme = item === minItem || item === maxItem;
        const tooltip = `${item.label}：${item.value} ${temperatureLabel(item.value)}${item.note ? `，${item.note}` : ""}`;
        return `
          <div class="temperature-day ${temperatureTone(item.value)} ${isToday ? "today" : ""} ${isExtreme ? "extreme" : ""}" title="${escapeHtml(tooltip)}" style="--score:${item.value}%">
            <i></i>
            <span>${escapeHtml(item.label)}</span>
            ${isToday || isExtreme ? `<b>${isToday ? "今日" : item === minItem ? "最低" : "最高"}</b>` : ""}
          </div>
        `;
      }).join("")}
    </div>
    <div class="temperature-history-tags">
      <span class="${temperatureTone(minItem.value)}">最低 ${escapeHtml(minItem.label)} ${minItem.value} ${temperatureLabel(minItem.value)}</span>
      <span class="${temperatureTone(today.value)}">当前 ${today.value} ${today.tag || temperatureLabel(today.value)}</span>
      <span class="${temperatureTone(maxItem.value)}">最高 ${escapeHtml(maxItem.label)} ${maxItem.value} ${temperatureLabel(maxItem.value)}</span>
    </div>
  `;
}

function numericChange(item = {}) {
  if (Number.isFinite(item.change)) return Number(item.change);
  if (Number.isFinite(item.changePercent)) return Number(item.changePercent);
  const raw = String(item.changeText || item.value || "").replace("%", "");
  const parsed = Number.parseFloat(raw);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatHeatChange(item = {}) {
  if (item.changeText) return String(item.changeText);
  const value = numericChange(item);
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function heatmapTone(item = {}) {
  const value = numericChange(item);
  if (value > 0.05) return "positive";
  if (value < -0.05) return "negative";
  return "neutral";
}

function fallbackHeatmaps(market = {}) {
  // 这里原本硬编码了一组美股行业（AI算力 -5.82% …）和一组港股行业
  // （特种化工 -10.79% …）。而 market.marketHeatmaps 这个键从来不存在，
  // 所以兜底 100% 命中——那些数字每天原样显示，且与同页真实的
  // 「纳斯达克 +1.00%」直接打架。宁可少显示一组，也不能编数字。
  const aShare = (market.hotSectors || []).slice(0, 10).map((item, index) => ({
    name: item.name,
    changeText: item.changeText,
    size: index < 2 ? "lg" : index < 6 ? "md" : "sm",
    note: (item.leaders || []).slice(0, 3).join(" / ")
  }));

  // 美股这组改用真实的宽基指数（我们确实有这份数据），而不是编造行业涨跌。
  const US_NAMES = ["道琼斯", "纳斯达克", "标普500"];
  const overseas = (market.globalMarkets || [])
    .filter((item) => US_NAMES.includes(item.name) && !item.dirty &&
                      item.changeText && item.changeText !== "--")
    .map((item, index) => ({
      name: item.name,
      changeText: item.changeText,
      size: index === 0 ? "lg" : "md"
    }));

  const groups = [];
  if (overseas.length) {
    groups.push({ market: "美股", subtitle: "隔夜宽基指数", items: overseas });
  }
  groups.push({ market: "A股", subtitle: "今日收盘板块", items: aShare });
  // 港股：没有数据源就不渲染这一组。
  return groups;
}

function renderMarketHeatmap(market = {}) {
  const groups = Array.isArray(market.marketHeatmaps) && market.marketHeatmaps.length
    ? market.marketHeatmaps
    : fallbackHeatmaps(market);

  $("#marketHeatmap").innerHTML = groups.map((group) => `
    <section class="heatmap-market">
      <div class="heatmap-market-head">
        <strong>${escapeHtml(group.market)}</strong>
        <span>${escapeHtml(group.subtitle || "")}</span>
      </div>
      <div class="heatmap-grid">
        ${(group.items || []).map((item) => {
          const change = formatHeatChange(item);
          const tooltip = `${item.name} ${change}${item.note ? ` · ${item.note}` : ""}`;
          return `
            <article class="heatmap-tile ${heatmapTone(item)} ${escapeHtml(item.size || "md")}" title="${escapeHtml(tooltip)}">
              <strong>${escapeHtml(item.name)}</strong>
              <span>${escapeHtml(change)}</span>
              ${item.note ? `<em>${escapeHtml(item.note)}</em>` : ""}
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `).join("");
}

function fallbackEventTimeline(market = {}) {
  const date = market.tradingDate ? market.tradingDate.slice(5) : "最新";
  // 事件解读已移到 insights.json，market.json 只保留客观数据。
  const events = (window.__insights && window.__insights.eventReads) || [];
  const newsEvents = events.slice(0, 5).map((item, index) => ({
    date,
    time: index < 2 ? "15:00" : "盘后",
    title: item.title,
    category: item.type,
    impact: index === 0 ? "利好" : item.type === "公告" ? "中性" : "观察",
    markets: ["A股"],
    tags: item.impactedStocks || []
  }));
  return {
    title: "核心事件时间轴",
    subtitle: "按事件对市场情绪的影响排序",
    summary: "事件轴用于解释情绪温度变化：先看宏观/地缘/政策，再看行业催化和上市公司公告，最后落到可交易板块。",
    days: [{ date, events: newsEvents, summary: "当前交易日核心事件汇总。" }]
  };
}

function normalizeTimelineDays(timeline = {}) {
  if (Array.isArray(timeline.days) && timeline.days.length) {
    return timeline.days.map((day) => ({
      date: safe(day.date || day.label, "--"),
      title: safe(day.title, ""),
      summary: safe(day.summary, timeline.summary || ""),
      events: Array.isArray(day.events) ? day.events : []
    }));
  }
  const dates = Array.isArray(timeline.dates) && timeline.dates.length
    ? timeline.dates
    : [...new Set((timeline.events || []).map((item) => item.date).filter(Boolean))];
  return dates.map((date) => ({
    date,
    summary: timeline.summary || "",
    events: (timeline.events || []).filter((item) => item.date === date)
  })).filter((day) => day.events.length);
}

function renderTimelineDay(timeline, days, activeIndex, activeEventIndex) {
  const activeDay = days[activeIndex] || days[days.length - 1];
  const events = activeDay.events || [];
  const defaultFocusIndex = Math.max(0, events.findIndex((item) => item.focus));
  const focusIndex = Number.isInteger(activeEventIndex) ? activeEventIndex : defaultFocusIndex;
  const focus = events[focusIndex] || events[0] || {};
  const impactClass = (impact) => String(impact || "").includes("利空") ? "bad" : String(impact || "").includes("利好") ? "good" : "watch";
  const count = days.reduce((sum, day) => sum + (day.events || []).length, 0);
  const sourceText = timeline.source
    ? `${safe(timeline.market, "A股")} · ${timeline.source}`
    : `${safe(timeline.market, "A股")} · 截至 ${activeDay.date} 共 ${count} 条`;
  const detailText = focus.detail
    || (focus.title && activeDay.summary ? `${focus.title}：${activeDay.summary}` : "")
    || activeDay.summary
    || timeline.summary
    || focus.title
    || "该交易日事件影响仍需结合盘面确认。";

  $("#eventTimeline").innerHTML = `
    <div class="timeline-head">
      <div>
        <strong>${escapeHtml(timeline.title || "核心事件时间轴")}</strong>
        <span>${escapeHtml(timeline.subtitle || "连续20个交易日核心事件复盘")}</span>
      </div>
      <em>${escapeHtml(sourceText)}</em>
    </div>
    <div class="timeline-date-strip" role="tablist" aria-label="核心事件日期">
      ${days.map((day, index) => `
        <button class="timeline-date-btn ${index === activeIndex ? "active" : ""}" type="button" data-date-index="${index}" role="tab" aria-selected="${index === activeIndex}">
          ${escapeHtml(day.date)}
        </button>
      `).join("")}
    </div>
    <div class="timeline-day-stage">
      <div class="timeline-date-rail">${escapeHtml(activeDay.date)}</div>
      <div class="timeline-event-row">
        ${events.map((item, index) => `
          <article class="timeline-event ${item === focus ? "focus" : ""}" data-event-index="${index}" role="button" tabindex="0" aria-label="查看 ${escapeHtml(item.title)} 的解读">
            <time>${escapeHtml(item.date || activeDay.date)} ${escapeHtml(item.time || "")}</time>
            <strong>${escapeHtml(item.title)}</strong>
            <div class="timeline-event-tags">
              <span>${escapeHtml(item.category || "事件")}</span>
              <span class="${impactClass(item.impact)}">${escapeHtml(item.impact || "观察")}</span>
            </div>
          </article>
        `).join("")}
      </div>
    </div>
    <div class="timeline-detail">
      <button class="timeline-collapse" type="button">收起</button>
      <div class="timeline-detail-tags">
        ${(focus.markets || [timeline.market || "A股"]).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
        ${(focus.tags || []).slice(0, 5).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
      </div>
      <p>${escapeHtml(detailText)}</p>
      ${timeline.sourceNote ? `<small>${escapeHtml(timeline.sourceNote)}</small>` : ""}
    </div>
  `;

  document.querySelectorAll(".timeline-date-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const nextIndex = Number(button.dataset.dateIndex);
      if (Number.isFinite(nextIndex)) renderTimelineDay(timeline, days, nextIndex);
    });
  });
  document.querySelectorAll(".timeline-event").forEach((card) => {
    const openEvent = () => {
      const nextEventIndex = Number(card.dataset.eventIndex);
      if (Number.isFinite(nextEventIndex)) renderTimelineDay(timeline, days, activeIndex, nextEventIndex);
    };
    card.addEventListener("click", openEvent);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openEvent();
      }
    });
  });
  const collapse = document.querySelector(".timeline-collapse");
  const detail = document.querySelector(".timeline-detail");
  if (collapse && detail) {
    collapse.addEventListener("click", () => {
      detail.classList.toggle("collapsed");
      collapse.textContent = detail.classList.contains("collapsed") ? "展开" : "收起";
    });
  }
  const activeButton = document.querySelector(".timeline-date-btn.active");
  if (activeButton) activeButton.scrollIntoView({ block: "nearest", inline: "end" });
}

function renderEventTimeline(market = {}) {
  const timeline = market.eventTimeline || fallbackEventTimeline(market);
  const days = normalizeTimelineDays(timeline).slice(-20);
  if (!days.length) {
    $("#eventTimeline").innerHTML = "";
    return;
  }
  const preferredIndex = days.findIndex((day) => day.events.some((event) => event.focus));
  renderTimelineDay(timeline, days, preferredIndex >= 0 ? preferredIndex : days.length - 1);
}

function displayMetric(rawValue, parsedValue, suffix = "") {
  if (parsedValue !== null && parsedValue !== undefined) return `${parsedValue}${suffix}`;
  return recentText(rawValue, "最近收盘样本");
}

function buildDecisionTriggers(temp, topSector, volume = {}) {
  const sectorName = safe(topSector.name, "强势主线");
  const volumeState = recentText(volume.change, "最近收盘量能");
  return [
    {
      title: "可加仓条件",
      text: `指数站稳分时均线，${sectorName}核心股回踩不破并再次放量。`
    },
    {
      title: "低吸条件",
      text: "强势股首次分歧缩量，板块强度仍在前三，尾盘承接不破关键均线。"
    },
    {
      title: "回避条件",
      text: `${volumeState.includes("-") ? "成交额转弱" : "量能未明显放大"}、后排冲高回落、核心股跌破5日线时降低出手频率。`
    },
    {
      title: "仓位节奏",
      text: temp.value >= 64 ? "情绪活跃时可用标准仓跟随核心。" : "当前更适合小仓确认，先看持续性再提高仓位。"
    }
  ];
}

function renderDecisionHub(market = {}) {
  const topSector = getTopSector(market.hotSectors);
  const topIndex = getTopIndex(market.indices);
  const styleRows = deriveStyleRows(market);
  const temp = getTemperature(market);
  const volume = market.volumeAnalysis || {};
  const sentiment = market.sentiment || {};
  const action = temp.value >= 64 ? "进攻" : temp.value >= 48 ? "选择性试错" : "防守观察";
  const primaryStyle = styleRows.map((item) => item.value).filter(Boolean).join(" · ");
  const sectorName = recentText(topSector.name, "强势板块");
  const headline = `${action}模式：${sectorName}领跑，${safe(topIndex.name, "核心指数")}${safe(topIndex.changeText, "")}`;

  $("#decisionHeadline").textContent = headline;
  $("#decisionSummary").textContent = `当前风格为 ${primaryStyle || "待确认"}。交易上先看主线核心股的分歧承接，后排补涨只做快进快出。`;
  $("#decisionInsights").innerHTML = [
    ["指数强弱", `${recentText(topIndex.name, "核心指数")} ${recentText(topIndex.changeText, "")}`, "领涨指数决定短线风格权重。"],
    ["主线强度", `${sectorName} ${safe(topSector.changeText, "")}`, `强度 ${safe(topSector.strength, "--")}，观察核心股是否继续带队。`],
    ["市场宽度", `涨 ${displayMetric(sentiment.upCount, temp.upCount)} / 跌 ${displayMetric(sentiment.downCount, temp.downCount)}`, "涨跌家数用于确认指数上涨是否有赚钱效应。"],
    ["涨停生态", `涨停 ${displayMetric(sentiment.limitUp, temp.limitUp)} / 跌停 ${displayMetric(sentiment.limitDown, temp.limitDown)}`, `连板 ${recentText(sentiment.consecutiveBoards, "最近收盘样本")}，炸板率 ${displayMetric(sentiment.breakRate, temp.breakRate, "%")}。`],
    ["量能状态", `${recentText(volume.today, "最近收盘成交额")} / ${recentText(volume.change, "最近收盘量能")}`, recentText(volume.summary, "采用最近一次A股收盘后成交额样本，用于判断量能方向。")],
    ["策略偏好", temp.value >= 64 ? "核心趋势股优先" : "分歧确认后再动手", "只做强势主线中辨识度最高、风险位最清晰的标的。"]
  ].map(([label, value, note]) => `
    <article class="decision-insight">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <p>${escapeHtml(note)}</p>
    </article>
  `).join("");

  $("#decisionTriggers").innerHTML = buildDecisionTriggers(temp, topSector, volume).map((item) => `
    <div class="decision-trigger">
      <strong>${escapeHtml(item.title)}</strong>
      <span>${escapeHtml(item.text)}</span>
    </div>
  `).join("");

  $("#decisionGrid").innerHTML = [
    ["市场状态", action, temp.value >= 64 ? "up" : temp.value >= 48 ? "flat" : "down"],
    ["主线方向", sectorName, "accent"],
    ["量能信号", recentText(volume.change, "最近收盘量能"), "flat"],
    ["明日动作", temp.value >= 64 ? "强股回踩低吸" : temp.value >= 48 ? "小仓确认" : "等待放量", "orange"]
  ].map(([label, value, cls]) => `
    <div class="decision-pill ${cls}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `).join("");

  $("#temperatureScore").textContent = temp.value;
  $("#temperatureLabel").textContent = temp.label;
  $("#temperatureRing").style.setProperty("--temperature", `${temp.value}%`);
  $("#temperatureMeta").innerHTML = [
    ["上涨", displayMetric(sentiment.upCount, temp.upCount)],
    ["下跌", displayMetric(sentiment.downCount, temp.downCount)],
    ["涨停", displayMetric(sentiment.limitUp, temp.limitUp)],
    ["跌停", displayMetric(sentiment.limitDown, temp.limitDown)],
    ["连板", recentText(sentiment.consecutiveBoards, "最近收盘样本")],
    ["炸板率", displayMetric(sentiment.breakRate, temp.breakRate, "%")]
  ].map(([label, value]) => `
    <div><span>${label}</span><strong>${escapeHtml(value)}</strong></div>
  `).join("");
  $("#temperatureBrief").innerHTML = `
    <strong>温度解读：</strong>
    <span>${escapeHtml(temperatureBrief(temp.label))}</span>
  `;
  renderTemperatureHistory(sentiment, temp);
  $("#temperatureSources").innerHTML = (sentiment.sources || ["东方财富收盘样本", "同花顺复核", "雪球复核"]).map((source) => `
    <span>${escapeHtml(placeholderWords.reduce((text, word) => text.replaceAll(word, "复核"), String(source)))}</span>
  `).join("");
}

function renderConsensus(market = {}) {
  const host = $("#consensusGrid");
  if (!host) return;
  const insights = window.__insights;
  const masterList = (insights && insights.masters) || [];

  // Votes are recounted here from the masters' own picks rather than trusting
  // consensus.picks, so the number on screen always matches the opinions shown.
  const votes = new Map();
  masterList.forEach((entry) => {
    (entry.picks || []).forEach((pick) => {
      const key = String(pick).trim();
      if (!key) return;
      votes.set(key, (votes.get(key) || 0) + 1);
    });
  });

  if (!votes.size) {
    host.innerHTML = emptyState("暂无投委会共识", INSIGHTS_HINT);
    return;
  }

  const voterCount = masterList.filter((entry) => (entry.picks || []).length).length || 1;
  const poolByName = new Map(((insights && insights.stockPool) || []).map((item) => [item.name, item]));

  const items = [...votes.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, count]) => {
      const pooled = poolByName.get(name) || {};
      return {
        name,
        count,
        score: Math.round((count / voterCount) * 100),
        code: pooled.code || "",
        sector: pooled.sector || "",
        action: pooled.action || "",
        horizon: pooled.horizon || ""
      };
    });

  host.innerHTML = items.map((item) => `
    <article class="consensus-item">
      <div class="consensus-score">${item.score}<span>%</span></div>
      <div>
        <div class="consensus-name">${escapeHtml(item.name)} ${item.code ? `<span>${escapeHtml(item.code)}</span>` : ""}</div>
        <p>${escapeHtml([item.sector, item.action].filter(Boolean).join(" · ") || "未进入股票池")}</p>
        <div class="tag-row">
          <span class="stock-ticker">${item.count} / ${voterCount} 位大师点名</span>
          ${item.horizon ? `<span class="stock-ticker">${escapeHtml(item.horizon)}</span>` : ""}
        </div>
      </div>
    </article>
  `).join("");
}

function renderQuickStats(items) {
  $("#quickStats").innerHTML = (items || []).map((item) => {
    const cls = item.color ? "" : tone(item.changePercent);
    const style = item.color ? ` style="color:${item.color}"` : "";
    return `
      <div class="quick-stat-item">
        <div class="quick-stat-value ${cls}"${style}>${safe(item.valueText)}</div>
        <div class="quick-stat-label">${escapeHtml(item.label)}</div>
      </div>
    `;
  }).join("");
}

function indexByName(items, name) {
  return (items || []).find((item) => item.name === name) || {};
}

function avgChange(items, names) {
  // 同 getTopIndex：陈旧/脏值不能进任何均值，否则会污染风格判定和情绪温度。
  const values = names
    .map((name) => indexByName(items, name))
    .filter(isUsableIndex)
    .map((item) => item.changePercent);
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function scoreFromDiff(diff) {
  if (!Number.isFinite(diff)) return 50;
  return Math.max(8, Math.min(92, Math.round(50 + diff * 22)));
}

function renderStyleMatrix(market, insights) {
  const matrix = deriveStyleRows(market);

  $("#styleMatrix").innerHTML = matrix.map((item) => `
    <div class="style-row">
      <div class="style-row-top">
        <span>${escapeHtml(item.label)}</span>
        <strong>${escapeHtml(item.value)}</strong>
      </div>
      <div class="style-track">
        <div class="style-fill" style="width:${Number(item.score) || 50}%"></div>
      </div>
      <div class="style-axis"><span>${escapeHtml(item.left || "")}</span><span>${escapeHtml(item.right || "")}</span></div>
    </div>
  `).join("");

  $("#styleSignals").innerHTML = matrix.map((item) => `
    <div class="mini-list-item">
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
    </div>
  `).join("");

  // 模型生成的 styleVerdict 一直被丢弃：prompt 要了、schema 校验了、
  // normalize 截断了，然后没人渲染——同时这里显示一句机械拼接的模板串。
  // 模型那份带具体数字和陈旧标注，比模板串有信息量得多。
  const verdict = insights && insights.styleVerdict;
  const mechanical = matrix.map((item) => `${item.label}：${item.value}`).join("；")
    + "。交易上优先选择与主风格共振的趋势强势股。";

  if (verdict && verdict.summary) {
    const tags = Array.isArray(verdict.tags) ? verdict.tags.filter(Boolean) : [];
    $("#styleSummary").innerHTML = `
      ${verdict.title ? `<strong class="style-verdict-title">${escapeHtml(verdict.title)}</strong>` : ""}
      <span class="style-verdict-body">${escapeHtml(verdict.summary)}</span>
      ${tags.length ? `<span class="style-verdict-tags">${
        tags.map((t) => `<em>${escapeHtml(t)}</em>`).join("")}</span>` : ""}
    `;
  } else {
    // 没有洞察时退回机械描述——比空白强，也如实反映"还没生成"。
    $("#styleSummary").textContent = mechanical;
  }
}

function renderIndices(items) {
  chartInstances.forEach((chart) => chart.dispose());
  chartInstances = [];
  $("#indicesGrid").innerHTML = (items || []).map((item, index) => {
    const cls = tone(item.changePercent);
    const tag = cls === "up" ? "UP" : cls === "down" ? "DOWN" : "FLAT";
    return `
      <div class="card index-card">
        <div class="index-card-header">
          <span class="index-name">${escapeHtml(item.name)}</span>
          <span class="index-tag ${cls}">${tag}</span>
        </div>
        <div class="index-value">${escapeHtml(item.valueText)}</div>
        <div class="index-change ${cls}">
          <i class="fas ${arrowIcon(item.changePercent)}"></i>
          ${escapeHtml(item.changeText)}
        </div>
        <div class="index-chart-mini" id="chartIndex${index}"></div>
      </div>
    `;
  }).join("");

  (items || []).forEach((item, index) => {
    const lineColor = Number(item.changePercent) >= 0 ? colors.up : colors.down;
    renderSparkline($(`#chartIndex${index}`), item.sparkline, lineColor);
  });
}

function renderMasters(insights) {
  const host = $("#masterGrid");
  if (!host) return;
  const generated = insights && Array.isArray(insights.masters) ? insights.masters : [];
  if (!generated.length) {
    host.innerHTML = emptyState("暂无大师观点", INSIGHTS_HINT);
    return;
  }
  // `masters` (the local roster) supplies avatar/category/icon; the quote,
  // tags and picks must come from the generated file — never from a default.
  const roster = new Map(masters.map((item) => [item.name, item]));
  const items = generated.map((entry) => {
    const base = roster.get(entry.name) || {};
    return {
      name: entry.name,
      category: entry.category || base.category || "投资风格",
      icon: base.icon || "fa-user",
      avatar: base.avatar || (entry.name || "?").slice(0, 1),
      avatarStyle: base.avatarStyle || "linear-gradient(135deg,#4a4a4a,#2a2a2a)",
      quote: entry.quote || "",
      tags: Array.isArray(entry.tags) ? entry.tags : [],
      picks: Array.isArray(entry.picks) ? entry.picks : []
    };
  });
  host.innerHTML = items.map((item) => `
    <div class="master-card">
      <div class="master-category"><i class="fas ${item.icon}"></i> ${escapeHtml(item.category)}</div>
      <div class="master-name">
        <div class="master-avatar" style="background:${item.avatarStyle}">${escapeHtml(item.avatar)}</div>
        ${escapeHtml(item.name)}
      </div>
      <div class="master-quote">${escapeHtml(item.quote)}</div>
      <div class="master-tag-row">
        ${item.tags.map((tag) => `<span class="master-tag">${escapeHtml(tag)}</span>`).join("")}
      </div>
      <div class="master-picks">
        <div class="master-picks-label"><i class="fas fa-bullseye"></i> 建议关注 / 买入观察</div>
        <div class="master-picks-row">
          ${item.picks.map((pick, index) => `<span class="master-pick">${escapeHtml(pick)}<span class="master-pick-tag ${index === 0 ? "up" : "defense"}">${index === 0 ? "核心" : "观察"}</span></span>`).join("")}
        </div>
      </div>
    </div>
  `).join("");
}

function renderVolume(volume = {}) {
  const bars = volume.bars || [];
  $("#volumeKpis").innerHTML = `
    <div class="volume-kpi"><span>最近收盘成交</span><strong>${escapeHtml(recentText(volume.today, "最近收盘样本"))}</strong></div>
    <div class="volume-kpi"><span>前一交易日</span><strong>${escapeHtml(recentText(volume.previous, "最近收盘样本"))}</strong></div>
    <div class="volume-kpi"><span>变化</span><strong>${escapeHtml(recentText(volume.change, "最近收盘量能"))}</strong></div>
  `;
  $("#volumeBars").innerHTML = `
    <div class="volume-chart">
      ${bars.map((item) => `
        <div class="volume-column" title="${escapeHtml(item.label)} ${escapeHtml(item.amountText || "")}">
          <div class="volume-column-bar" style="height:${Math.max(4, Math.min(100, Number(item.value) || 0))}%"></div>
          <span>${escapeHtml(item.label)}</span>
        </div>
      `).join("")}
    </div>
    <div class="volume-note">柱状图口径：沪深两市成交额，最多保留近 22 个交易日。序列按交易日归并——
      东财日线可用时一次性回填整段，否则每个交易日累积一根，缺失的交易日会留空而不是被顶掉。</div>
  `;
  $("#volumeSummary").textContent = recentText(volume.summary, "成交量采用最近一次A股收盘后样本。");
  $("#volumeChecklist").innerHTML = [
    ["放量上涨", "趋势强势股可提高关注优先级", true],
    ["缩量上涨", "注意追高性价比，等待回踩确认", false],
    ["放量下跌", "降低仓位，观察是否出现系统性风险", false]
  ].map(([title, text, checked]) => `
    <li class="checklist-item">
      <div class="checklist-box ${checked ? "checked" : ""}">${checked ? '<i class="fas fa-check"></i>' : ""}</div>
      <div class="checklist-text"><strong>${title}：</strong>${text}</div>
    </li>
  `).join("");
}

function renderSectors(items = []) {
  $("#hotSectors").innerHTML = items.map((item) => `
    <article class="sector-item">
      <div class="sector-rank">${escapeHtml(item.rank)}</div>
      <div>
        <div class="sector-head">
          <strong>${escapeHtml(item.name)}</strong>
          <span>${escapeHtml(item.changeText)}</span>
        </div>
        <div class="strength-track"><div class="strength-fill" style="width:${Number(item.strength) || 0}%"></div></div>
        <p>${escapeHtml(item.reason)}</p>
        <div class="leader-label">推荐板块龙头</div>
        <div class="tag-row">${(item.leaders || []).map((leader) => `<span class="stock-ticker">${escapeHtml(leader)}</span>`).join("")}</div>
      </div>
    </article>
  `).join("");
}

function renderMainlineBoard(items = []) {
  const topItems = [...items]
    .sort((a, b) => (Number(b.strength) || 0) - (Number(a.strength) || 0))
    .slice(0, 5);

  $("#mainlineBoard").innerHTML = topItems.map((item, index) => {
    const action = index === 0 ? "核心主攻" : index <= 2 ? "分歧低吸" : "观察补涨";
    return `
      <article class="mainline-item">
        <div class="mainline-rank">0${index + 1}</div>
        <div class="mainline-body">
          <div class="mainline-head">
            <strong>${escapeHtml(item.name)}</strong>
            <span>${escapeHtml(action)}</span>
          </div>
          <div class="mainline-score">
            <div style="width:${clamp(Number(item.strength) || 0, 0, 100)}%"></div>
          </div>
          <p>${escapeHtml(item.reason)}</p>
          <div class="mainline-foot">
            <span>强度 ${escapeHtml(item.strength || "--")}</span>
            <div class="tag-row">${(item.leaders || []).slice(0, 4).map((leader) => `<span class="stock-ticker">${escapeHtml(leader)}</span>`).join("")}</div>
          </div>
        </div>
      </article>
    `;
  }).join("");
}

function renderFundFlows(items = []) {
  $("#fundFlows").innerHTML = items.map((item) => `
    <div class="flow-item">
      <div>
        <strong>${escapeHtml(item.name)}</strong>
        <p>${escapeHtml(item.summary)}</p>
      </div>
      <span class="${escapeHtml(item.direction || "flat")}">${escapeHtml(item.valueText)}</span>
    </div>
  `).join("");
}

function renderValuations(items = []) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) {
    $("#valuationGrid").innerHTML = emptyState("暂无估值数据", "需要安装 akshare 后运行 update_data.py。");
    return;
  }
  $("#valuationGrid").innerHTML = list.map((item) => `
    <article class="valuation-card${item.stale ? " stale" : ""}">
      <div class="valuation-name">
        ${escapeHtml(item.name)}
        ${item.stale ? `<span class="stale-flag">数据陈旧</span>` : ""}
      </div>
      <div class="valuation-metrics">
        <span>PE(TTM) <strong>${escapeHtml(item.pe || "--")}</strong></span>
        <span>PB <strong>${escapeHtml(item.pb || "--")}</strong></span>
        ${item.pePercentile !== undefined
          ? `<span>PE 全历史分位 <strong>${escapeHtml(String(item.pePercentile))}%</strong></span>` : ""}
        ${item.pePercentile10y !== undefined
          ? `<span>PE 近10年分位 <strong>${escapeHtml(String(item.pePercentile10y))}%</strong></span>` : ""}
        ${item.pbPercentile !== undefined
          ? `<span>PB 全历史分位 <strong>${escapeHtml(String(item.pbPercentile))}%</strong></span>` : ""}
      </div>
      ${item.asOf ? `<p class="valuation-asof">数据日期 ${escapeHtml(item.asOf)}</p>` : ""}
      ${item.url
        ? `<a class="source-link" href="${safeUrl(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.source || "估值来源")}</a>`
        : (item.source ? `<span class="source-link">${escapeHtml(item.source)}</span>` : "")}
    </article>
  `).join("");
}

function renderStockAnalysis(items) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) {
    $("#stockAnalysis").innerHTML = emptyState("暂无板块解读", INSIGHTS_HINT);
    return;
  }
  $("#stockAnalysis").innerHTML = list.map((item) => `
    <div class="stock-analysis-item">
      <span>${escapeHtml(item.sustainability || "解读")}</span>
      <div>
        <strong>${escapeHtml(item.name)}</strong>
        <p>${escapeHtml(item.reason)}</p>
      </div>
    </div>
  `).join("");
}

function renderSentiment(sentiment = {}) {
  const items = [
    ["上涨家数", sentiment.upCount, "up"],
    ["下跌家数", sentiment.downCount, "down"],
    ["涨停数", sentiment.limitUp, "up"],
    ["跌停数", sentiment.limitDown, "down"],
    ["连板股", sentiment.consecutiveBoards, "flat"],
    ["炸板率", sentiment.breakRate, "flat"]
  ];
  $("#sentimentGrid").innerHTML = items.map(([label, value, cls]) => `
    <div class="sentiment-item">
      <span>${label}</span>
      <strong class="${cls}">${escapeHtml(recentText(value, "最近收盘样本"))}</strong>
    </div>
  `).join("");
  $("#sentimentSummary").textContent = recentText(sentiment.summary, "市场情绪采用最近一次A股收盘后样本。");
  if (sentiment.sources && sentiment.sources.length) {
    $("#sentimentSummary").textContent += ` 数据源：${sentiment.sources.map((source) => recentText(source, "公开行情源")).join(" / ")}。`;
  }
}

function renderAbnormalMoves(items) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) {
    $("#abnormalMoves").innerHTML = emptyState("暂无异常波动解读", INSIGHTS_HINT);
    return;
  }
  $("#abnormalMoves").innerHTML = list.map((item) => `
    <article class="abnormal-card">
      <strong>${escapeHtml(item.type)}</strong>
      <div class="tag-row">${(item.items || []).map((stock) => `<span class="stock-ticker">${escapeHtml(stock)}</span>`).join("")}</div>
      <p>${escapeHtml(item.note)}</p>
    </article>
  `).join("");
}

function renderLhb(items = []) {
  $("#lhbList").innerHTML = (items || []).slice(0, 12).map((item) => `
    <article class="lhb-item">
      <div>
        <strong>${escapeHtml(item.name)}</strong>
        <span>${escapeHtml(item.code)} · ${escapeHtml(item.date)}</span>
      </div>
      <p>${escapeHtml(item.reason)}</p>
      <div class="lhb-meta">
        <span class="${tone(Number.parseFloat(item.changeText))}">${escapeHtml(item.changeText)}</span>
        <span>净额 ${escapeHtml(item.netAmountText)}</span>
      </div>
    </article>
  `).join("");
}

function renderEvents(items) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) {
    $("#eventList").innerHTML = emptyState("暂无事件解读", INSIGHTS_HINT);
    return;
  }
  $("#eventList").innerHTML = list.map((item) => `
    <article class="event-item">
      <span>${escapeHtml(item.type)}</span>
      <div>
        <p>${escapeHtml(item.title)}</p>
        <div class="tag-row">${(item.impactedStocks || []).map((stock) => `<span class="stock-ticker">${escapeHtml(stock)}</span>`).join("")}</div>
      </div>
    </article>
  `).join("");
}

function renderAdvice(advice) {
  const host = $("#adviceGrid");
  if (!host) return;
  if (!advice || (!advice.summary && !(advice.shortTerm || []).length)) {
    host.innerHTML = emptyState("暂无交易建议", INSIGHTS_HINT);
    return;
  }
  const cards = [
    { title: "短线 1-3 个交易日", icon: "fa-bolt", points: advice.shortTerm || [] },
    { title: "中线 1-3 个月", icon: "fa-route", points: advice.midTerm || [] }
  ].filter((card) => card.points.length);

  host.innerHTML = `
    ${advice.summary ? `<article class="card advice-card advice-summary">
      <div class="card-title"><i class="fas fa-compass"></i> 明日策略</div>
      <p>${escapeHtml(advice.summary)}</p>
    </article>` : ""}
    ${cards.map((card) => `
      <article class="card advice-card">
        <div class="card-title"><i class="fas ${card.icon}"></i> ${escapeHtml(card.title)}</div>
        <ul class="advice-points">
          ${card.points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}
        </ul>
      </article>
    `).join("")}
    ${advice.riskControl ? `<article class="card advice-card advice-risk-card">
      <div class="card-title"><i class="fas fa-shield-halved"></i> 风控纪律</div>
      <p>${escapeHtml(advice.riskControl)}</p>
    </article>` : ""}
  `;
}

function renderScenarios(market = {}) {
  const topSector = getTopSector(market.hotSectors);
  const temp = getTemperature(market);
  const sectorName = safe(topSector.name, "强势主线");
  const leaders = (topSector.leaders || []).slice(0, 3).join("、") || "板块核心股";
  const scenarios = [
    {
      title: "剧本A：指数放量上攻",
      icon: "fa-arrow-trend-up",
      bias: "进攻",
      text: `优先跟随 ${sectorName}，只看 ${leaders} 这类核心或中军。买点放在回踩不破 5 日线后的转强。`
    },
    {
      title: "剧本B：冲高回落",
      icon: "fa-arrows-left-right",
      bias: "防追高",
      text: "不追早盘一致性高开，等待主线核心股分歧承接。若后排明显掉队，降低交易频率。"
    },
    {
      title: "剧本C：缩量震荡",
      icon: "fa-hourglass-half",
      bias: temp.value >= 55 ? "轻仓试错" : "观望",
      text: "只做小仓位确认，仓位放在趋势强、成交活跃、风险位清晰的股票；无放量则保留现金。"
    }
  ];

  $("#scenarioGrid").innerHTML = scenarios.map((item) => `
    <article class="scenario-card">
      <div class="scenario-icon"><i class="fas ${item.icon}"></i></div>
      <div>
        <div class="scenario-head">
          <strong>${escapeHtml(item.title)}</strong>
          <span>${escapeHtml(item.bias)}</span>
        </div>
        <p>${escapeHtml(item.text)}</p>
      </div>
    </article>
  `).join("");
}

function renderGlobal(items) {
  $("#globalGrid").innerHTML = (items || []).map((item) => {
    const cls = tone(item.changePercent);
    return `
      <div class="global-card">
        <div class="global-name">${escapeHtml(item.name)}</div>
        <div class="global-value">${escapeHtml(item.valueText)}</div>
        <div class="global-change ${cls}">${escapeHtml(item.changeText)}</div>
      </div>
    `;
  }).join("");
}

function renderNews(items) {
  $("#newsGrid").innerHTML = (items || []).slice(0, 12).map((item, index) => {
    const number = String(index + 1).padStart(2, "0");
    const title = escapeHtml(item.title);
    const url = safeUrl(item.url);
    const titleHtml = url
      ? `<a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;
    return `
      <div class="news-item">
        <div class="news-header"><div class="news-num">${number}</div></div>
        <div class="news-headline">${titleHtml}</div>
        <div class="news-meta">
          <span>${escapeHtml(item.source, "新闻")}</span>
          <span>${escapeHtml(item.publishedAtText, "最新")}</span>
        </div>
        <div class="news-impact">
          <span>${escapeHtml(item.impactNote || "可能影响：相关主题板块")}</span>
          <div class="tag-row">${(item.impactedStocks || []).map((stock) => `<span class="stock-ticker">${escapeHtml(stock)}</span>`).join("")}</div>
        </div>
      </div>
    `;
  }).join("");
}

function renderStockPool(items) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) {
    $("#stockPoolGrid").innerHTML = emptyState("暂无股票池", INSIGHTS_HINT);
    return;
  }
  $("#stockPoolGrid").innerHTML = list.slice(0, 15).map((item, index) => {
    const buyTrigger = item.buyTrigger || (index < 5 ? "回踩5日线不破后转强" : "放量突破平台后再确认");
    const sellTrigger = item.sellTrigger || item.risk || "跌破关键均线或板块退潮";
    const position = item.position || (index < 5 ? "标准仓" : index < 10 ? "轻仓试错" : "观察仓");
    return `
    <article class="stock-pool-card">
      <div class="stock-pool-top">
        <div>
          <strong>${escapeHtml(item.name)}</strong>
          <!-- code 现在是可选的（数据里常常没有板块龙头的代码），
               缺失时不要渲染出一个孤零零的 " · " 分隔符 -->
          <span>${escapeHtml([item.code, item.sector].filter(Boolean).join(" · "))}</span>
        </div>
        <em>${escapeHtml(item.action)}</em>
      </div>
      <p>${escapeHtml(item.logic)}</p>
      <div class="trade-plan">
        <div><span>买点</span><strong>${escapeHtml(buyTrigger)}</strong></div>
        <div><span>卖点</span><strong>${escapeHtml(sellTrigger)}</strong></div>
        <div><span>仓位</span><strong>${escapeHtml(position)}</strong></div>
      </div>
      <div class="stock-pool-bottom">
        <span>${escapeHtml(item.horizon)}</span>
        <span>${escapeHtml(item.sector)}</span>
      </div>
    </article>
  `;
  }).join("");
}

function renderStrategy() {
  $("#strategyPanel").innerHTML = strategyItems.map(([title, content, cls]) => `
    <div class="strategy-card ${cls}">
      <div class="strategy-title">${title}</div>
      <div class="strategy-content">${content}</div>
    </div>
  `).join("");

  $("#checklist").innerHTML = checklist.map(([title, text, checked]) => `
    <li class="checklist-item">
      <div class="checklist-box ${checked ? "checked" : ""}">${checked ? '<i class="fas fa-check"></i>' : ""}</div>
      <div class="checklist-text"><strong>${title}：</strong>${text}</div>
    </li>
  `).join("");
}

function renderRisks() {
  $("#riskGrid").innerHTML = risks.map((item) => `
    <div class="risk-item">
      <div class="risk-icon ${item.tone}"><i class="fas ${item.icon}"></i></div>
      <div>
        <div class="risk-title">${item.title}</div>
        <div class="risk-desc">${item.desc}</div>
      </div>
    </div>
  `).join("");
}

function bindNav() {
  $("#navToggle").addEventListener("click", () => {
    $("#navLinks").classList.toggle("open");
  });
  document.querySelectorAll(".nav-links a").forEach((link) => {
    link.addEventListener("click", () => $("#navLinks").classList.remove("open"));
  });
}

async function boot() {
  bindNav();
  renderStrategy();
  renderRisks();

  try {
    const [rawMarket, rawNews, fileInsights] = await Promise.all([
      readJson("market.json"),
      readJson("news.json"),
      readJsonOptional("insights.json")
    ]);
    const market = sanitizePlaceholders(rawMarket);
    market.indices = sanitizeIndices(market.indices);
    market.globalMarkets = sanitizeIndices(market.globalMarkets);
    const news = sanitizePlaceholders(rawNews);
    // A pasted-in-browser result takes precedence only when it is newer than
    // the file on disk, so a fresh save_insights.py run isn't shadowed by a
    // stale localStorage entry.
    const stored = insightsFromStorage();
    const insights = pickNewerInsights(fileInsights, stored);
    window.__insights = insights;
    window.__market = market;

    renderDataBanner(market, insights);
    renderInsightsPanel(market, insights);
    renderMasters(insights);
    renderHero(market);
    renderDecisionHub(market);
    renderEventTimeline(market);
    renderConsensus(market);
    renderIndices(market.indices);
    renderStyleMatrix(market, insights);
    renderVolume(market.volumeAnalysis);
    renderMarketHeatmap(market);
    renderMainlineBoard(market.hotSectors);
    renderSectors(market.hotSectors);
    renderFundFlows(market.fundFlows);
    renderValuations(market.valuations);
    renderStockAnalysis(insights && insights.sectorReads);
    renderSentiment(market.sentiment);
    renderAbnormalMoves(insights && insights.abnormalMoves);
    renderLhb(market.lhb);
    renderEvents(insights && insights.eventReads);
    renderAdvice(insights && insights.tradingAdvice);
    renderScenarios(market);
    renderStockPool(insights && insights.stockPool);
    renderGlobal(market.globalMarkets);
    renderNews(news.items);
  } catch (error) {
    $("#heroSubtitle").textContent = "数据读取失败，请确认 market.json 和 news.json 已存在。";
    console.error(error);
  }
}

/* ---------------------------------------------------------------------------
 * 洞察生成面板：把 market.json 拼成提示词 → 用户贴进 chat → 结果粘回来。
 * 与 make_prompt.py / save_insights.py 保持同一套 digest、schema 和校验规则。
 * ------------------------------------------------------------------------- */

function buildFactsDigest(market = {}) {
  const lines = [];
  const push = (line) => lines.push(line);
  const sentiment = market.sentiment || {};

  push(`交易日：${market.tradingDateText || market.tradingDate || "--"}`);
  push(`行情状态：${market.marketStatus || "--"}｜两市成交额：${market.turnoverText || "--"}`);

  const status = market.fetchStatus || {};
  const stale = Object.entries(status).filter(([, value]) => value && value.state !== "live");
  if (stale.length) {
    push("");
    push("⚠️ 数据新鲜度警告：以下板块本次未能抓到最新数据，可能沿用上一交易日的值——");
    stale.forEach(([key, value]) => push(`  - ${key}：${value.state}｜${value.detail || "无细节"}`));
    push("  评论时请勿把上述板块的数字当作今日真实情况，必要时明确指出该项数据缺失。");
  }

  push("");
  push("【指数】");
  (market.indices || []).forEach((item) => {
    push(`  ${item.name}: ${item.valueText} ${item.changeText}${item.stale ? "（数据陈旧，非今日）" : ""}`);
  });

  if ((market.globalMarkets || []).length) {
    push("");
    push("【外围市场】");
    market.globalMarkets.forEach((item) => {
      push(`  ${item.name}: ${item.valueText} ${item.changeText}${item.stale ? "（数据陈旧）" : ""}`);
    });
  }

  push("");
  push("【市场宽度与涨停生态】");
  push(`  上涨 ${sentiment.upCount || "--"} 家｜下跌 ${sentiment.downCount || "--"} 家`);
  push(`  涨停 ${sentiment.limitUp || "--"} 家｜跌停 ${sentiment.limitDown || "--"} 家｜炸板率 ${sentiment.breakRate || "--"}`);
  push(`  连板情况：${sentiment.consecutiveBoards || "--"}`);
  if (sentiment.boardLadder) {
    push(`  连板天梯：${Object.entries(sentiment.boardLadder).map(([k, v]) => `${k}板 ${v}只`).join("、")}`);
  }
  if ((sentiment.limitUpLeaders || []).length) {
    push(`  涨停梯队龙头：${sentiment.limitUpLeaders.map((x) => `${x.name}(${x.board}板/${x.sector})`).join("、")}`);
  }
  push(`  统计口径：${sentiment.limitCaliber || "--"}`);

  const volume = market.volumeAnalysis || {};
  if (volume.today) {
    push("");
    push("【成交量】");
    push(`  今日 ${volume.today}｜上一交易日 ${volume.previous || "--"}｜变化 ${volume.change || "--"}`);
  }

  if ((market.hotSectors || []).length) {
    push("");
    push("【板块涨幅榜】（strength = 50 + 5×涨幅%，仅由涨幅线性换算，不含其他信息）");
    market.hotSectors.forEach((item) => {
      push(`  ${item.rank}. ${item.name} ${item.changeText}｜强度 ${item.strength}｜龙头 ${(item.leaders || []).slice(0, 3).join("、")}`);
    });
  }

  if ((market.fundFlows || []).length) {
    push("");
    push("【主力资金流向】");
    market.fundFlows.forEach((item) => push(`  ${item.name}: ${item.valueText}｜${item.summary || ""}`));
  }

  if ((market.valuations || []).length) {
    push("");
    push("【指数估值】（分位数由历史序列计算，非主观判断）");
    market.valuations.forEach((item) => {
      const parts = [`  ${item.name}: PE(TTM) ${item.pe || "--"}｜PB ${item.pb || "--"}`];
      if (item.pePercentile !== undefined) parts.push(`｜PE全历史分位 ${item.pePercentile}%`);
      if (item.pePercentile10y !== undefined) parts.push(`｜近10年分位 ${item.pePercentile10y}%`);
      if (item.stale) parts.push("（数据陈旧，非今日）");
      else if (item.asOf) parts.push(`｜数据日期 ${item.asOf}`);
      push(parts.join(""));
    });
  }

  if ((market.lhb || []).length) {
    push("");
    push("【龙虎榜】");
    market.lhb.slice(0, 10).forEach((item) => {
      push(`  ${item.name} ${item.changeText || ""}｜净额 ${item.netAmountText || "--"}｜${item.reason || ""}`);
    });
  }

  return lines.join("\n");
}

function promptSkeleton(tradingDate) {
  return {
    tradingDate,
    styleVerdict: { title: "小票弱于权重，价值防守占优", summary: "引用具体数字说明风格判定依据", tags: ["防守", "缩量"] },
    sectorReads: [{ name: "（来自板块涨幅榜的板块名）", reason: "该板块走强/走弱的原因", sustainability: "中" }],
    masters: [{ name: "（来自大师名单）", quote: "以该大师口吻的一句点评，落到具体数字或板块", tags: ["关键词1", "关键词2"], picks: ["点名的标的"] }],
    consensus: { agreementPct: 0, note: "共识说明", picks: [{ name: "标的名", code: "代码", votes: 0 }] },
    tradingAdvice: { summary: "明日策略总结", shortTerm: ["短线要点"], midTerm: ["中线要点"], riskControl: "风控纪律" },
    stockPool: [{ code: "600000", name: "标的名", sector: "所属板块", action: "回踩关注", horizon: "短线", logic: "入选逻辑", risk: "风险点" }],
    abnormalMoves: [{ type: "逆势股", items: ["个股名"], note: "说明" }],
    eventReads: [{ type: "政策", title: "事件描述", impactedStocks: ["受影响标的"] }]
  };
}

function buildPrompt(market, mastersCfg) {
  const digest = buildFactsDigest(market);
  const roster = (mastersCfg.masters || [])
    .map((m) => `  - ${m.name}（${m.category}）：${m.style}`)
    .join("\n");
  const tradingDate = market.tradingDate;

  return `你是一名 A 股盘后复盘助手。下面是某个交易日的**客观盘面数据**，请据此生成一份结构化的复盘洞察。

================ 盘面数据（唯一事实来源）================
${digest}
========================================================

================ 大师人设名单 ================
请让下列人物分别以各自的交易风格点评当日盘面。每人只说自己风格关心的东西——
价值派不该讨论连板高度，情绪派不该讨论自由现金流。观点之间应当出现真实分歧，
不要让所有人都得出同一个结论。

${roster}
==============================================

================ 硬性要求 ================
1. **只使用上面给出的数据**。不得引入任何未在数据中出现的个股、板块、指数或数字。
   如果某项数据标注了"数据陈旧"或出现在新鲜度警告里，不要拿它当今日事实，
   可以在相应位置说明该数据缺失。
2. 每条点评都要落到具体数字或具体板块，禁止"注意风险""保持谨慎"这类空话。
3. \`consensus.agreementPct\` 必须由你自己在 masters 里的点名统计得出：
   被点名最多的标的的得票数 ÷ 给出 picks 的大师人数 × 100，四舍五入取整。
   不要凭感觉写一个好看的百分比。
4. \`stockPool\` 里的个股必须来自上面出现过的板块龙头、涨停梯队或龙虎榜名单。
5. 只输出 JSON，不要输出任何解释文字、不要用 markdown 代码块包裹。
6. \`tradingDate\` 必须严格填写为 "${tradingDate}"。
==========================================

================ 输出格式 ================
严格按以下结构输出（字段含义见注释，实际输出不要带注释）：

${JSON.stringify(promptSkeleton(tradingDate), null, 2)}
==========================================

现在开始，直接输出 JSON：`;
}

// Mirrors extract_json() in save_insights.py — chat UIs wrap JSON in fences and
// prose, and a naive lastIndexOf("}") truncates any nested object.
function extractJson(text) {
  if (!text || !text.trim()) throw new Error("输入为空");

  const fence = text.indexOf("```");
  if (fence !== -1) {
    const rest = text.slice(fence + 3);
    const newline = rest.indexOf("\n");
    if (newline !== -1) {
      const body = rest.slice(newline + 1);
      const close = body.indexOf("```");
      if (close !== -1) {
        const candidate = body.slice(0, close).trim();
        if (candidate.startsWith("{")) return JSON.parse(candidate);
      }
    }
  }

  const start = text.indexOf("{");
  if (start === -1) throw new Error("没找到 JSON 对象（输入里没有 '{'）");

  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let i = start; i < text.length; i += 1) {
    const char = text[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') inString = true;
    else if (char === "{") depth += 1;
    else if (char === "}") {
      depth -= 1;
      if (depth === 0) return JSON.parse(text.slice(start, i + 1));
    }
  }
  throw new Error("JSON 花括号不配平，回复可能被截断了——让模型重新输出完整 JSON");
}

function validateInsights(data, mastersCfg) {
  const errors = [];
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    return ["顶层必须是 JSON 对象"];
  }
  ["tradingDate", "styleVerdict", "masters", "tradingAdvice", "stockPool"].forEach((key) => {
    const value = data[key];
    const empty = value === undefined || value === null || value === "" ||
      (Array.isArray(value) && !value.length);
    if (empty) errors.push(`${key}: 必填字段缺失或为空`);
  });
  if (data.masters && !Array.isArray(data.masters)) errors.push("masters: 应为数组");
  if (data.stockPool && !Array.isArray(data.stockPool)) errors.push("stockPool: 应为数组");
  if (data.styleVerdict && typeof data.styleVerdict === "object" && !data.styleVerdict.title) {
    errors.push("styleVerdict.title: 必填字段缺失或为空");
  }

  const roster = new Set((mastersCfg.masters || []).map((m) => m.name));
  if (Array.isArray(data.masters)) {
    data.masters.forEach((item, index) => {
      if (!item || typeof item !== "object") {
        errors.push(`masters[${index}]: 应为对象`);
        return;
      }
      if (!item.quote) errors.push(`masters[${index}].quote: 必填字段缺失或为空`);
      if (item.name && !roster.has(item.name)) {
        errors.push(`masters[${index}].name: '${item.name}' 不在大师名单里`);
      }
    });
  }
  return errors;
}

async function renderInsightsPanel(market, insights) {
  const panel = $("#insightsPanel");
  if (!panel) return;

  const mastersCfg = (await readJsonOptional("config/masters.json")) || { masters };
  const prompt = buildPrompt(market, mastersCfg);

  const badge = $("#insightsBadge");
  const meta = $("#insightsMeta");
  if (insights) {
    const mismatch = insights.tradingDate && market.tradingDate &&
      insights.tradingDate !== market.tradingDate;
    if (badge) {
      badge.textContent = mismatch ? `${insights.tradingDate} 的旧洞察` : "已生成";
      badge.classList.toggle("warn", Boolean(mismatch));
    }
    if (meta) {
      meta.textContent = `当前：${insights.tradingDate || "?"}｜${(insights.masters || []).length} 条观点` +
        `${insights.generatedAtText ? `｜${insights.generatedAtText}` : ""}`;
    }
  } else {
    if (badge) badge.textContent = "未生成";
    if (meta) meta.textContent = "当前：无";
  }

  const setStatus = (element, text, tone) => {
    if (!element) return;
    element.textContent = text;
    element.className = `insights-status ${tone || ""}`;
  };

  $("#copyPromptBtn").addEventListener("click", async () => {
    const status = $("#copyStatus");
    try {
      await navigator.clipboard.writeText(prompt);
      setStatus(status, `已复制 ${prompt.length} 字符`, "ok");
    } catch (error) {
      // clipboard API needs a secure context; file:// and plain http hosts fail.
      $("#promptPreview").hidden = false;
      $("#promptPreview").textContent = prompt;
      setStatus(status, "浏览器拒绝了剪贴板权限，提示词已展开在下方，请手动复制", "warn");
    }
  });

  $("#viewPromptBtn").addEventListener("click", () => {
    const preview = $("#promptPreview");
    preview.hidden = !preview.hidden;
    if (!preview.hidden) preview.textContent = prompt;
  });

  $("#applyInsightsBtn").addEventListener("click", () => {
    const result = $("#insightsResult");
    const raw = $("#insightsInput").value;
    let parsed;
    try {
      parsed = extractJson(raw);
    } catch (error) {
      result.className = "insights-result error";
      result.innerHTML = `<strong>解析失败：</strong>${escapeHtml(error.message)}<br>
        提示：让模型重新输出一次，强调「只输出 JSON，不要任何解释文字」。`;
      return;
    }
    const errors = validateInsights(parsed, mastersCfg);
    if (errors.length) {
      result.className = "insights-result error";
      result.innerHTML = `<strong>校验未通过（${errors.length} 处），未应用：</strong>
        <ul>${errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("")}</ul>
        把这些报错贴回 chat 让它修正后重试。`;
      return;
    }
    const now = new Date();
    parsed.generatedAt = now.toISOString();
    parsed.generatedAtText = now.toLocaleString("zh-CN", { hour12: false });
    parsed.generator = "browser-paste";
    localStorage.setItem("marketInsights", JSON.stringify(parsed));

    const mismatch = parsed.tradingDate && market.tradingDate &&
      parsed.tradingDate !== market.tradingDate;
    result.className = "insights-result ok";
    result.innerHTML = `<strong>已应用。</strong>交易日 ${escapeHtml(parsed.tradingDate || "?")}｜
      大师观点 ${(parsed.masters || []).length} 条｜股票池 ${(parsed.stockPool || []).length} 只
      ${mismatch ? `<br><span class="warn-text">注意：该洞察对应 ${escapeHtml(parsed.tradingDate)}，与行情日期 ${escapeHtml(market.tradingDate)} 不一致。</span>` : ""}`;

    window.__insights = parsed;
    renderDataBanner(market, parsed);
    renderMasters(parsed);
    renderStockAnalysis(parsed.sectorReads);
    renderAbnormalMoves(parsed.abnormalMoves);
    renderEvents(parsed.eventReads);
    renderAdvice(parsed.tradingAdvice);
    renderStockPool(parsed.stockPool);
    renderConsensus(market);
  });

  $("#downloadInsightsBtn").addEventListener("click", () => {
    const current = window.__insights;
    if (!current) {
      setStatus($("#copyStatus"), "还没有可下载的洞察内容", "warn");
      return;
    }
    const blob = new Blob([JSON.stringify(current, null, 2) + "\n"], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "insights.json";
    link.click();
    URL.revokeObjectURL(url);
  });

  $("#clearInsightsBtn").addEventListener("click", () => {
    localStorage.removeItem("marketInsights");
    window.__insights = null;
    $("#insightsInput").value = "";
    const result = $("#insightsResult");
    result.className = "insights-result";
    result.textContent = "已清除本机保存的洞察内容，刷新页面后将回到 insights.json（若存在）。";
  });
}

function pickNewerInsights(fileInsights, stored) {
  if (!fileInsights) return stored;
  if (!stored) return fileInsights;
  const fileTime = Date.parse(fileInsights.generatedAt || "") || 0;
  const storedTime = Date.parse(stored.generatedAt || "") || 0;
  return storedTime > fileTime ? stored : fileInsights;
}

function renderDataBanner(market = {}, insights) {
  const host = $("#dataBanner");
  if (!host) return;
  const alerts = [];

  // The original tool's worst failure mode: commentary from one session shown
  // above quotes from another, with nothing telling the reader.
  if (insights && insights.tradingDate && market.tradingDate &&
      insights.tradingDate !== market.tradingDate) {
    alerts.push({
      level: "warn",
      text: `洞察内容对应 ${insights.tradingDate}，但行情数据是 ${market.tradingDate} —— 大师观点与交易建议并非针对今日盘面。`
    });
  }
  if (!insights) {
    alerts.push({ level: "info", text: `尚未生成洞察内容。${INSIGHTS_HINT}` });
  }

  // 告警要分级。以前 `state !== "live"` 一刀切，把四种语义压成同一句话：
  //   fallback/missing — 硬编码的占位数字，根本不是任何交易日的真实行情
  //   stale            — 旧但真实（上一交易日的值）
  //   partial          — 部分标的没取到，其余是新的
  // 结果最严重的 fallback 和最无害的 partial 长得一模一样，而且因为海外指数
  // 结构上天天 partial，这条黄条永远亮着，等于没有告警。
  const status = market.fetchStatus || {};
  const entries = Object.entries(status).filter(([, v]) => v && v.state);
  const fabricated = entries.filter(([, v]) => v.state === "fallback" || v.state === "missing");
  const carried = entries.filter(([, v]) => v.state === "stale");
  const partial = entries.filter(([, v]) => v.state === "partial");

  if (fabricated.length) {
    alerts.push({
      level: "error",
      text: `以下板块本次与上次抓取均失败，显示的是占位默认值，不代表任何真实交易日：${
        fabricated.map(([k]) => k).join("、")}`
    });
  }
  if (carried.length) {
    alerts.push({
      level: "warn",
      text: `以下板块沿用上一交易日的数据：${
        carried.map(([k, v]) => v.source ? `${k}（${v.source}）` : k).join("、")}`
    });
  }
  // partial 只是"部分标的没取到"，卡片上已有逐条角标，不值得占一条横幅。
  if (partial.length) {
    alerts.push({
      level: "info",
      text: `部分标的未取到最新值（${partial.map(([k]) => k).join("、")}），相关卡片已单独标注。`
    });
  }

  if (!alerts.length) {
    host.innerHTML = "";
    host.hidden = true;
    return;
  }
  host.hidden = false;
  host.innerHTML = alerts.map((alert) => `
    <div class="data-banner ${alert.level}">
      <i class="fas ${alert.level === "warn" ? "fa-triangle-exclamation" : "fa-circle-info"}"></i>
      <span>${escapeHtml(alert.text)}</span>
    </div>
  `).join("");
}

window.addEventListener("resize", () => {
  chartInstances.forEach((chart) => chart.resize());
});

boot();
