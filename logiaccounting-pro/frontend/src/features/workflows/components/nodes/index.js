/**
 * Workflow Node Components
 */

export { BaseNode } from './BaseNode';
export { TriggerNode } from './TriggerNode';
export { ActionNode } from './ActionNode';
export { ConditionNode } from './ConditionNode';
export { ParallelNode } from './ParallelNode';
export { DelayNode } from './DelayNode';
export { EndNode } from './EndNode';

export const nodeTypes = {
  trigger: () => import('./TriggerNode').then(m => m.TriggerNode),
  action: () => import('./ActionNode').then(m => m.ActionNode),
  condition: () => import('./ConditionNode').then(m => m.ConditionNode),
  parallel: () => import('./ParallelNode').then(m => m.ParallelNode),
  delay: () => import('./DelayNode').then(m => m.DelayNode),
  end: () => import('./EndNode').then(m => m.EndNode),
};
