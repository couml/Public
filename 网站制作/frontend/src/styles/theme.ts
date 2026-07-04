export const theme = {
  primaryColor: '#1677ff',
  borderRadius: 6,
  colorBgContainer: '#ffffff',
  fontFamily:
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
} as const;

export type AppTheme = typeof theme;
