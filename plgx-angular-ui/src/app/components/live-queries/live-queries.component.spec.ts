import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { LiveQueriesComponent } from './live-queries.component';

describe('LiveQueriesComponent', () => {
  let component: LiveQueriesComponent;
  let fixture: ComponentFixture<LiveQueriesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ LiveQueriesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LiveQueriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
