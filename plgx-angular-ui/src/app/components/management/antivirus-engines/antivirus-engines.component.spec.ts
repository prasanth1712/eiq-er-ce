import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AntivirusEnginesComponent } from './antivirus-engines.component';

describe('AntivirusEnginesComponent', () => {
  let component: AntivirusEnginesComponent;
  let fixture: ComponentFixture<AntivirusEnginesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AntivirusEnginesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AntivirusEnginesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
