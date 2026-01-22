/**
 * Condition Operator Types Configuration
 */

export const OPERATOR_TYPES = {
  EQUALS: 'equals',
  NOT_EQUALS: 'not_equals',
  GREATER_THAN: 'greater_than',
  GREATER_THAN_OR_EQUALS: 'greater_than_or_equals',
  LESS_THAN: 'less_than',
  LESS_THAN_OR_EQUALS: 'less_than_or_equals',
  CONTAINS: 'contains',
  NOT_CONTAINS: 'not_contains',
  STARTS_WITH: 'starts_with',
  ENDS_WITH: 'ends_with',
  IN: 'in',
  NOT_IN: 'not_in',
  IS_EMPTY: 'is_empty',
  IS_NOT_EMPTY: 'is_not_empty',
  MATCHES_REGEX: 'matches_regex',
  BETWEEN: 'between',
};

export const OPERATOR_CONFIGS = {
  [OPERATOR_TYPES.EQUALS]: {
    label: 'equals',
    symbol: '==',
    valueType: 'any',
    description: 'Value equals',
  },
  [OPERATOR_TYPES.NOT_EQUALS]: {
    label: 'not equals',
    symbol: '!=',
    valueType: 'any',
    description: 'Value does not equal',
  },
  [OPERATOR_TYPES.GREATER_THAN]: {
    label: 'greater than',
    symbol: '>',
    valueType: 'number',
    description: 'Value is greater than',
  },
  [OPERATOR_TYPES.GREATER_THAN_OR_EQUALS]: {
    label: 'greater than or equals',
    symbol: '>=',
    valueType: 'number',
    description: 'Value is greater than or equal to',
  },
  [OPERATOR_TYPES.LESS_THAN]: {
    label: 'less than',
    symbol: '<',
    valueType: 'number',
    description: 'Value is less than',
  },
  [OPERATOR_TYPES.LESS_THAN_OR_EQUALS]: {
    label: 'less than or equals',
    symbol: '<=',
    valueType: 'number',
    description: 'Value is less than or equal to',
  },
  [OPERATOR_TYPES.CONTAINS]: {
    label: 'contains',
    symbol: 'contains',
    valueType: 'string',
    description: 'String contains substring',
  },
  [OPERATOR_TYPES.NOT_CONTAINS]: {
    label: 'does not contain',
    symbol: 'not contains',
    valueType: 'string',
    description: 'String does not contain substring',
  },
  [OPERATOR_TYPES.STARTS_WITH]: {
    label: 'starts with',
    symbol: 'starts with',
    valueType: 'string',
    description: 'String starts with',
  },
  [OPERATOR_TYPES.ENDS_WITH]: {
    label: 'ends with',
    symbol: 'ends with',
    valueType: 'string',
    description: 'String ends with',
  },
  [OPERATOR_TYPES.IN]: {
    label: 'is in',
    symbol: 'in',
    valueType: 'array',
    description: 'Value is in list',
  },
  [OPERATOR_TYPES.NOT_IN]: {
    label: 'is not in',
    symbol: 'not in',
    valueType: 'array',
    description: 'Value is not in list',
  },
  [OPERATOR_TYPES.IS_EMPTY]: {
    label: 'is empty',
    symbol: 'is empty',
    valueType: 'none',
    description: 'Value is empty or null',
  },
  [OPERATOR_TYPES.IS_NOT_EMPTY]: {
    label: 'is not empty',
    symbol: 'is not empty',
    valueType: 'none',
    description: 'Value is not empty',
  },
  [OPERATOR_TYPES.MATCHES_REGEX]: {
    label: 'matches regex',
    symbol: 'matches',
    valueType: 'regex',
    description: 'Value matches regular expression',
  },
  [OPERATOR_TYPES.BETWEEN]: {
    label: 'is between',
    symbol: 'between',
    valueType: 'range',
    description: 'Value is between two numbers',
  },
};

export const CONDITION_GROUP_TYPES = {
  ALL: 'all',
  ANY: 'any',
  NONE: 'none',
};

export const CONDITION_GROUP_LABELS = {
  [CONDITION_GROUP_TYPES.ALL]: 'All conditions match (AND)',
  [CONDITION_GROUP_TYPES.ANY]: 'Any condition matches (OR)',
  [CONDITION_GROUP_TYPES.NONE]: 'No conditions match (NOT)',
};

export const getOperatorConfig = (type) => OPERATOR_CONFIGS[type] || OPERATOR_CONFIGS[OPERATOR_TYPES.EQUALS];

export const getOperatorsForType = (fieldType) => {
  const typeMapping = {
    string: [
      OPERATOR_TYPES.EQUALS,
      OPERATOR_TYPES.NOT_EQUALS,
      OPERATOR_TYPES.CONTAINS,
      OPERATOR_TYPES.NOT_CONTAINS,
      OPERATOR_TYPES.STARTS_WITH,
      OPERATOR_TYPES.ENDS_WITH,
      OPERATOR_TYPES.IS_EMPTY,
      OPERATOR_TYPES.IS_NOT_EMPTY,
      OPERATOR_TYPES.MATCHES_REGEX,
    ],
    number: [
      OPERATOR_TYPES.EQUALS,
      OPERATOR_TYPES.NOT_EQUALS,
      OPERATOR_TYPES.GREATER_THAN,
      OPERATOR_TYPES.GREATER_THAN_OR_EQUALS,
      OPERATOR_TYPES.LESS_THAN,
      OPERATOR_TYPES.LESS_THAN_OR_EQUALS,
      OPERATOR_TYPES.BETWEEN,
      OPERATOR_TYPES.IS_EMPTY,
      OPERATOR_TYPES.IS_NOT_EMPTY,
    ],
    boolean: [
      OPERATOR_TYPES.EQUALS,
      OPERATOR_TYPES.NOT_EQUALS,
    ],
    array: [
      OPERATOR_TYPES.CONTAINS,
      OPERATOR_TYPES.NOT_CONTAINS,
      OPERATOR_TYPES.IS_EMPTY,
      OPERATOR_TYPES.IS_NOT_EMPTY,
    ],
    any: Object.keys(OPERATOR_CONFIGS),
  };

  return typeMapping[fieldType] || typeMapping.any;
};
