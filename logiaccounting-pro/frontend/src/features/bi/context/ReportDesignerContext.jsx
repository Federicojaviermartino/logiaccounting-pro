/**
 * Report Designer Context
 * Global state management for report builder
 */

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

const ReportDesignerContext = createContext(null);

// Initial state
const initialState = {
  // Report metadata
  report: {
    id: null,
    name: 'Untitled Report',
    description: '',
    categoryId: null,
  },

  // Data source
  dataSource: {
    type: 'internal',
    tables: [],
    joins: [],
  },

  // Query definition
  query: {
    fields: [],
    filters: [],
    grouping: [],
    sorting: [],
    limit: null,
  },

  // Layout
  layout: {
    pageSize: 'a4',
    orientation: 'portrait',
    margins: { top: 20, right: 20, bottom: 20, left: 20 },
    components: [],
  },

  // Designer state
  designer: {
    selectedComponentId: null,
    zoom: 100,
    showGrid: true,
    snapToGrid: true,
    gridSize: 10,
  },

  // Preview data
  preview: {
    data: null,
    loading: false,
    error: null,
  },

  // History for undo/redo
  history: {
    past: [],
    future: [],
  },

  // Dirty flag
  isDirty: false,
};

// Action types
const ACTIONS = {
  SET_REPORT: 'SET_REPORT',
  UPDATE_REPORT: 'UPDATE_REPORT',
  SET_DATA_SOURCE: 'SET_DATA_SOURCE',
  ADD_TABLE: 'ADD_TABLE',
  REMOVE_TABLE: 'REMOVE_TABLE',
  ADD_JOIN: 'ADD_JOIN',
  REMOVE_JOIN: 'REMOVE_JOIN',
  ADD_FIELD: 'ADD_FIELD',
  REMOVE_FIELD: 'REMOVE_FIELD',
  UPDATE_FIELD: 'UPDATE_FIELD',
  ADD_FILTER: 'ADD_FILTER',
  REMOVE_FILTER: 'REMOVE_FILTER',
  UPDATE_FILTER: 'UPDATE_FILTER',
  SET_GROUPING: 'SET_GROUPING',
  SET_SORTING: 'SET_SORTING',
  ADD_COMPONENT: 'ADD_COMPONENT',
  REMOVE_COMPONENT: 'REMOVE_COMPONENT',
  UPDATE_COMPONENT: 'UPDATE_COMPONENT',
  MOVE_COMPONENT: 'MOVE_COMPONENT',
  SELECT_COMPONENT: 'SELECT_COMPONENT',
  SET_LAYOUT: 'SET_LAYOUT',
  SET_DESIGNER: 'SET_DESIGNER',
  SET_PREVIEW: 'SET_PREVIEW',
  UNDO: 'UNDO',
  REDO: 'REDO',
  RESET: 'RESET',
  LOAD_REPORT: 'LOAD_REPORT',
};

// Reducer
function reportDesignerReducer(state, action) {
  // Save to history for undo (except for certain actions)
  const saveToHistory = !['SET_PREVIEW', 'SELECT_COMPONENT', 'SET_DESIGNER', 'UNDO', 'REDO'].includes(action.type);

  let newState = state;

  switch (action.type) {
    case ACTIONS.SET_REPORT:
      newState = {
        ...state,
        report: { ...state.report, ...action.payload },
        isDirty: true,
      };
      break;

    case ACTIONS.UPDATE_REPORT:
      newState = {
        ...state,
        report: { ...state.report, ...action.payload },
        isDirty: true,
      };
      break;

    case ACTIONS.SET_DATA_SOURCE:
      newState = {
        ...state,
        dataSource: action.payload,
        isDirty: true,
      };
      break;

    case ACTIONS.ADD_TABLE:
      newState = {
        ...state,
        dataSource: {
          ...state.dataSource,
          tables: [...state.dataSource.tables, action.payload],
        },
        isDirty: true,
      };
      break;

    case ACTIONS.REMOVE_TABLE:
      newState = {
        ...state,
        dataSource: {
          ...state.dataSource,
          tables: state.dataSource.tables.filter(t => t.name !== action.payload),
          joins: state.dataSource.joins.filter(j =>
            j.leftTable !== action.payload && j.rightTable !== action.payload
          ),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.ADD_JOIN:
      newState = {
        ...state,
        dataSource: {
          ...state.dataSource,
          joins: [...state.dataSource.joins, { id: uuidv4(), ...action.payload }],
        },
        isDirty: true,
      };
      break;

    case ACTIONS.REMOVE_JOIN:
      newState = {
        ...state,
        dataSource: {
          ...state.dataSource,
          joins: state.dataSource.joins.filter(j => j.id !== action.payload),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.ADD_FIELD:
      newState = {
        ...state,
        query: {
          ...state.query,
          fields: [...state.query.fields, { id: uuidv4(), ...action.payload }],
        },
        isDirty: true,
      };
      break;

    case ACTIONS.REMOVE_FIELD:
      newState = {
        ...state,
        query: {
          ...state.query,
          fields: state.query.fields.filter(f => f.id !== action.payload),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.UPDATE_FIELD:
      newState = {
        ...state,
        query: {
          ...state.query,
          fields: state.query.fields.map(f =>
            f.id === action.payload.id ? { ...f, ...action.payload } : f
          ),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.ADD_FILTER:
      newState = {
        ...state,
        query: {
          ...state.query,
          filters: [...state.query.filters, { id: uuidv4(), ...action.payload }],
        },
        isDirty: true,
      };
      break;

    case ACTIONS.REMOVE_FILTER:
      newState = {
        ...state,
        query: {
          ...state.query,
          filters: state.query.filters.filter(f => f.id !== action.payload),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.UPDATE_FILTER:
      newState = {
        ...state,
        query: {
          ...state.query,
          filters: state.query.filters.map(f =>
            f.id === action.payload.id ? { ...f, ...action.payload } : f
          ),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.SET_GROUPING:
      newState = {
        ...state,
        query: { ...state.query, grouping: action.payload },
        isDirty: true,
      };
      break;

    case ACTIONS.SET_SORTING:
      newState = {
        ...state,
        query: { ...state.query, sorting: action.payload },
        isDirty: true,
      };
      break;

    case ACTIONS.ADD_COMPONENT:
      newState = {
        ...state,
        layout: {
          ...state.layout,
          components: [...state.layout.components, { id: uuidv4(), ...action.payload }],
        },
        isDirty: true,
      };
      break;

    case ACTIONS.REMOVE_COMPONENT:
      newState = {
        ...state,
        layout: {
          ...state.layout,
          components: state.layout.components.filter(c => c.id !== action.payload),
        },
        designer: {
          ...state.designer,
          selectedComponentId: state.designer.selectedComponentId === action.payload
            ? null
            : state.designer.selectedComponentId,
        },
        isDirty: true,
      };
      break;

    case ACTIONS.UPDATE_COMPONENT:
      newState = {
        ...state,
        layout: {
          ...state.layout,
          components: state.layout.components.map(c =>
            c.id === action.payload.id ? { ...c, ...action.payload } : c
          ),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.MOVE_COMPONENT:
      newState = {
        ...state,
        layout: {
          ...state.layout,
          components: state.layout.components.map(c =>
            c.id === action.payload.id
              ? { ...c, position: action.payload.position }
              : c
          ),
        },
        isDirty: true,
      };
      break;

    case ACTIONS.SELECT_COMPONENT:
      newState = {
        ...state,
        designer: { ...state.designer, selectedComponentId: action.payload },
      };
      break;

    case ACTIONS.SET_LAYOUT:
      newState = {
        ...state,
        layout: { ...state.layout, ...action.payload },
        isDirty: true,
      };
      break;

    case ACTIONS.SET_DESIGNER:
      newState = {
        ...state,
        designer: { ...state.designer, ...action.payload },
      };
      break;

    case ACTIONS.SET_PREVIEW:
      newState = {
        ...state,
        preview: action.payload,
      };
      break;

    case ACTIONS.UNDO:
      if (state.history.past.length === 0) return state;
      const previous = state.history.past[state.history.past.length - 1];
      return {
        ...previous,
        history: {
          past: state.history.past.slice(0, -1),
          future: [state, ...state.history.future],
        },
      };

    case ACTIONS.REDO:
      if (state.history.future.length === 0) return state;
      const next = state.history.future[0];
      return {
        ...next,
        history: {
          past: [...state.history.past, state],
          future: state.history.future.slice(1),
        },
      };

    case ACTIONS.RESET:
      return initialState;

    case ACTIONS.LOAD_REPORT:
      return {
        ...initialState,
        ...action.payload,
        isDirty: false,
        history: { past: [], future: [] },
      };

    default:
      return state;
  }

  // Save to history
  if (saveToHistory && newState !== state) {
    return {
      ...newState,
      history: {
        past: [...state.history.past.slice(-49), state], // Keep last 50 states
        future: [],
      },
    };
  }

  return newState;
}

// Provider component
export function ReportDesignerProvider({ children }) {
  const [state, dispatch] = useReducer(reportDesignerReducer, initialState);

  // Action creators
  const actions = {
    setReport: useCallback((report) =>
      dispatch({ type: ACTIONS.SET_REPORT, payload: report }), []),
    updateReport: useCallback((updates) =>
      dispatch({ type: ACTIONS.UPDATE_REPORT, payload: updates }), []),
    setDataSource: useCallback((dataSource) =>
      dispatch({ type: ACTIONS.SET_DATA_SOURCE, payload: dataSource }), []),
    addTable: useCallback((table) =>
      dispatch({ type: ACTIONS.ADD_TABLE, payload: table }), []),
    removeTable: useCallback((tableName) =>
      dispatch({ type: ACTIONS.REMOVE_TABLE, payload: tableName }), []),
    addJoin: useCallback((join) =>
      dispatch({ type: ACTIONS.ADD_JOIN, payload: join }), []),
    removeJoin: useCallback((joinId) =>
      dispatch({ type: ACTIONS.REMOVE_JOIN, payload: joinId }), []),
    addField: useCallback((field) =>
      dispatch({ type: ACTIONS.ADD_FIELD, payload: field }), []),
    removeField: useCallback((fieldId) =>
      dispatch({ type: ACTIONS.REMOVE_FIELD, payload: fieldId }), []),
    updateField: useCallback((field) =>
      dispatch({ type: ACTIONS.UPDATE_FIELD, payload: field }), []),
    addFilter: useCallback((filter) =>
      dispatch({ type: ACTIONS.ADD_FILTER, payload: filter }), []),
    removeFilter: useCallback((filterId) =>
      dispatch({ type: ACTIONS.REMOVE_FILTER, payload: filterId }), []),
    updateFilter: useCallback((filter) =>
      dispatch({ type: ACTIONS.UPDATE_FILTER, payload: filter }), []),
    setGrouping: useCallback((grouping) =>
      dispatch({ type: ACTIONS.SET_GROUPING, payload: grouping }), []),
    setSorting: useCallback((sorting) =>
      dispatch({ type: ACTIONS.SET_SORTING, payload: sorting }), []),
    addComponent: useCallback((component) =>
      dispatch({ type: ACTIONS.ADD_COMPONENT, payload: component }), []),
    removeComponent: useCallback((componentId) =>
      dispatch({ type: ACTIONS.REMOVE_COMPONENT, payload: componentId }), []),
    updateComponent: useCallback((component) =>
      dispatch({ type: ACTIONS.UPDATE_COMPONENT, payload: component }), []),
    moveComponent: useCallback((id, position) =>
      dispatch({ type: ACTIONS.MOVE_COMPONENT, payload: { id, position } }), []),
    selectComponent: useCallback((componentId) =>
      dispatch({ type: ACTIONS.SELECT_COMPONENT, payload: componentId }), []),
    setLayout: useCallback((layout) =>
      dispatch({ type: ACTIONS.SET_LAYOUT, payload: layout }), []),
    setDesigner: useCallback((settings) =>
      dispatch({ type: ACTIONS.SET_DESIGNER, payload: settings }), []),
    setPreview: useCallback((preview) =>
      dispatch({ type: ACTIONS.SET_PREVIEW, payload: preview }), []),
    undo: useCallback(() => dispatch({ type: ACTIONS.UNDO }), []),
    redo: useCallback(() => dispatch({ type: ACTIONS.REDO }), []),
    reset: useCallback(() => dispatch({ type: ACTIONS.RESET }), []),
    loadReport: useCallback((report) =>
      dispatch({ type: ACTIONS.LOAD_REPORT, payload: report }), []),
  };

  return (
    <ReportDesignerContext.Provider value={{ state, actions }}>
      {children}
    </ReportDesignerContext.Provider>
  );
}

// Custom hook
export function useReportDesigner() {
  const context = useContext(ReportDesignerContext);
  if (!context) {
    throw new Error('useReportDesigner must be used within ReportDesignerProvider');
  }
  return context;
}

export default ReportDesignerContext;
