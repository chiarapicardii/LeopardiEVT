import { Component, Input } from '@angular/core';
import { Mod, Reading } from '../../models/evt-models';
import { register } from '../../services/component-register.service';
import { Highlightable } from '../components-mixins';
import { AppConfig, EditionLevelType } from 'src/app/app.config';

@Component({
  selector: 'evt-reading',
  templateUrl: './reading.component.html',
  styleUrls: ['./reading.component.scss'],
})
@register(Reading)
export class ReadingComponent extends Highlightable {
  // Il punto esclamativo (!) toglie l'errore di inizializzazione mancante richiesto da TypeScript
  @Input() data!: Reading;
  @Input() editionLevel!: EditionLevelType;
  @Input() withDeletions!: boolean;
  @Input() selectedLayer!: string;

  public ModType = Mod;

  getLayerColor(changeLayer: any): string {
    // 1. Accediamo in sicurezza all'oggetto usando il safe navigation per evitare crash asincroni
    const editionConfig = (AppConfig as any).evtSettings?.edition;
    const layerColors = editionConfig?.changeSequenceView?.layerColors;
    
    if (!layerColors) {
      return 'black'; // Fallback sicuro durante il caricamento
    }

    // 2. Puliamo la stringa del testimone (es. "#F31" diventa "F31")
    const layerKey = changeLayer && typeof changeLayer === 'string' ? changeLayer.replace('#', '') : '';
    
    // 3. Leggiamo la chiave in modo flessibile per non far arrabbiare il compilatore
    if (layerKey && Object.prototype.hasOwnProperty.call(layerColors, layerKey)) {
      return (layerColors as any)[layerKey] || 'black';
    }

    return 'black';
  }
}