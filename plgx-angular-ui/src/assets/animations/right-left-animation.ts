import { trigger, state, style, transition,
    animate, group, query, stagger, keyframes
} from '@angular/animations';
const defaults = {
    delayEnter: '200ms',
    delayLeave: '0ms',
    timingEnter: '2s',
    timingLeave: '2s',
  };
export const flyInOutRTLAnimation = [
    trigger('flyInOutRTL', [
      state('true', style({ width: '*' })),
      state('false', style({ width: '0px' })),
      transition('false <=> true', animate(500))
      ]),
]
