/** Compact shield mark used in the app shell and sign-in page. */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none" aria-hidden="true">
      <rect x="1" y="1" width="34" height="34" rx="11" fill="#14233a" />
      <rect x="1" y="1" width="34" height="34" rx="11" stroke="#60A5FA" strokeOpacity=".22" />
      <path
        d="M18 7.5 27 11v6.1c0 5.3-3.7 9.5-9 11.4-5.3-1.9-9-6.1-9-11.4V11l9-3.5Z"
        fill="#60A5FA"
        fillOpacity=".14"
        stroke="#60A5FA"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="m14.2 17.8 2.5 2.5 5.2-5.3"
        stroke="#BAE6FD"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
