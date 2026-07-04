import type { Rule } from 'antd/es/form';

/**
 * Required field rule.
 * Usage: rules={[requiredRule('用户名')]}
 */
export function requiredRule(label: string): Rule {
  return {
    required: true,
    message: `请输入${label}`,
  };
}

/**
 * Email format validation rule.
 */
export const emailRule: Rule = {
  pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  message: '请输入有效的邮箱地址',
};

/**
 * Password rule: minimum 8 characters, must contain both letters and numbers.
 */
export const passwordRule: Rule = {
  min: 8,
  message: '密码至少8位，且需包含字母和数字',
};

/**
 * Password pattern validator (used in addition to min length).
 */
export const passwordPatternRule: Rule = {
  pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,}$/,
  message: '密码必须包含字母和数字，且至少8位',
};

/**
 * Chinese mainland phone number rule.
 */
export const phoneRule: Rule = {
  pattern: /^1[3-9]\d{9}$/,
  message: '请输入有效的手机号码',
};
