declare module 'react-grid-layout' {
  import * as React from 'react';
  import { CSSProperties } from 'react';

  export interface Layout {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    minW?: number;
    maxW?: number;
    minH?: number;
    maxH?: number;
    static?: boolean;
    isDraggable?: boolean;
    isResizable?: boolean;
  }

  export interface ResponsiveProps {
    className?: string;
    style?: CSSProperties;
    cols: { [key: string]: number };
    layouts: { [key: string]: Layout[] };
    rowHeight?: number;
    margin?: [number, number];
    containerPadding?: [number, number];
    draggableHandle?: string;
    draggableCancel?: string;
    isDraggable?: boolean;
    isResizable?: boolean;
    allowOverlap?: boolean;
    compactType?: 'vertical' | 'horizontal';
    preventCollision?: boolean;
    measureBeforeMount?: boolean;
    useCSSTransforms?: boolean;
    transformScale?: number;
    verticalCompact?: boolean;
    onLayoutChange?: (layout: Layout[]) => void;
  }

  export class Responsive extends React.Component<ResponsiveProps> {}

  export interface WidthProviderProps {
    measureBeforeMount?: boolean;
  }

  export function WidthProvider<P>(component: React.ComponentType<P>): React.ComponentType<P & WidthProviderProps>;
}
