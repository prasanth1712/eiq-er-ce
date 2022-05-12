import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AlertsUnderRuleComponent } from './alerts-under-rule.component';

describe('AlertsUnderRuleComponent', () => {
  let component: AlertsUnderRuleComponent;
  let fixture: ComponentFixture<AlertsUnderRuleComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AlertsUnderRuleComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AlertsUnderRuleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
