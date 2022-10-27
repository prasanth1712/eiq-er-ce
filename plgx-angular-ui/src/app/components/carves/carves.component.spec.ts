import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { CarvesComponent } from './carves.component';

describe('CarvesComponent', () => {
  let component: CarvesComponent;
  let fixture: ComponentFixture<CarvesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CarvesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CarvesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
