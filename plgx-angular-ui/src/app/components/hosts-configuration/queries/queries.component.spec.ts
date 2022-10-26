import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { QueriesComponent } from './queries.component';

describe('QueriesComponent', () => {
  let component: QueriesComponent;
  let fixture: ComponentFixture<QueriesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ QueriesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(QueriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
