import { Device } from './Device';

export interface Connection {
    id: string;
    from: Device;
    to: Device;
    strength: number;
}
