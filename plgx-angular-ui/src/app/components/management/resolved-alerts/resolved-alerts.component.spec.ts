import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ResolvedAlertsComponent } from './resolved-alerts.component';

describe('ResolvedAlertsComponent', () => {
  let component: ResolvedAlertsComponent;
  let fixture: ComponentFixture<ResolvedAlertsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ResolvedAlertsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ResolvedAlertsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
