import type { CSSProperties } from 'react'

/**
 * Q 版智能体「小微」——微众银行 AI 助手
 * 圆润机器人形象：微众蓝 + 暖白 + 可爱表情 + 领结
 */
export default function XiaoWei({
  size = 48,
  style,
}: {
  size?: number
  style?: CSSProperties
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      style={style}
      role="img"
      aria-label="小微 · 微众银行 AI 助手"
    >
      <defs>
        <linearGradient id="xw-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#6E9DFF" />
          <stop offset="1" stopColor="#3B6FE0" />
        </linearGradient>
        <linearGradient id="xw-face" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFFFFF" />
          <stop offset="1" stopColor="#EAF0FF" />
        </linearGradient>
      </defs>

      {/* 天线 */}
      <line x1="60" y1="14" x2="60" y2="26" stroke="#3B6FE0" strokeWidth="4" strokeLinecap="round" />
      <circle cx="60" cy="11" r="6" fill="#F6B93B" />

      {/* 身体（圆润大头） */}
      <rect x="22" y="24" width="76" height="72" rx="24" fill="url(#xw-body)" />

      {/* 耳朵 */}
      <circle cx="22" cy="58" r="9" fill="#3B6FE0" />
      <circle cx="98" cy="58" r="9" fill="#3B6FE0" />

      {/* 脸（屏幕） */}
      <rect x="34" y="38" width="52" height="44" rx="14" fill="url(#xw-face)" />

      {/* 眼睛 */}
      <circle cx="50" cy="56" r="4.5" fill="#2A3B5C" />
      <circle cx="70" cy="56" r="4.5" fill="#2A3B5C" />
      {/* 眼睛高光 */}
      <circle cx="51.5" cy="54.5" r="1.5" fill="#FFFFFF" />
      <circle cx="71.5" cy="54.5" r="1.5" fill="#FFFFFF" />

      {/* 腮红 */}
      <circle cx="44" cy="64" r="3.5" fill="#FFB4B4" opacity="0.7" />
      <circle cx="76" cy="64" r="3.5" fill="#FFB4B4" opacity="0.7" />

      {/* 微笑 */}
      <path d="M53 68 Q60 74 67 68" stroke="#2A3B5C" strokeWidth="2.5" strokeLinecap="round" fill="none" />

      {/* 领结 */}
      <path d="M60 86 L52 82 L52 90 Z" fill="#F6B93B" />
      <path d="M60 86 L68 82 L68 90 Z" fill="#F6B93B" />
      <circle cx="60" cy="86" r="2.5" fill="#E09B2B" />

      {/* 小手 */}
      <circle cx="32" cy="92" r="7" fill="#3B6FE0" />
      <circle cx="88" cy="92" r="7" fill="#3B6FE0" />
    </svg>
  )
}
