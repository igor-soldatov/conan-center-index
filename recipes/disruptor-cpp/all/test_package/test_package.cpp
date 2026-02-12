#include <Disruptor/Sequence.h>

int main()
{
    Disruptor::Sequence sequence;
    sequence.setValue(42);
    return sequence.value() == 42 ? 0 : 1;
}
