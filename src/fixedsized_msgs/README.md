# fixedsized_msgs

Fixed-size DDS message definitions for lwrclpy zero-copy experiments.

These IDL files intentionally avoid `string` and `sequence`. Text fields use
`FixedString*` structs with a byte capacity and a runtime `size`. Images and
point clouds use fixed-capacity arrays plus runtime counters such as
`point_count`.

The point cloud capacities are sized for common maximum profiles:

- Velodyne VLP-16: `16 * 2048`
- Velodyne VLP-32C: `32 * 2048`
- Velodyne HDL-64E: `64 * 2048`
- Velodyne VLS-128 / Alpha Prime: `128 * 2048`
- Ouster OS-1 / OS-2 128-channel: `128 * 2048`
- Hesai JT128 / AT128 / QT128: `128 * 2048`
- Hesai QT64: `64 * 2048`
- Hesai ATX: `256 * 2048`

Set the actual valid payload length in `point_count`; unused array entries are
padding for the fixed-size transport contract.
