export interface Device {
    id: string;
    name: string;
    ipAddress: string;
    macAddress: string;
    status: 'online' | 'offline';
}
